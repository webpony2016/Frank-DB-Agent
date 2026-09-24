from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import pytest
from conftest import approved_job, new_job, assignment_fields


@pytest.mark.parametrize("same", ["both", "crew", "equipment"])
def test_resource_conflicts(client, same):
    first, second = approved_job(client), approved_job(client)
    fields = assignment_fields(client)
    result = client.put(f"/api/jobs/{first['id']}/assignment", json=dict(fields, expected_version=first["version"]))
    assert result.status_code == 200
    boot = client.get("/api/bootstrap").json()
    if same == "crew":
        fields["equipment_id"] = boot["equipment"][1]["id"]
    if same == "equipment":
        fields["crew_id"] = boot["crews"][1]["id"]
    result = client.put(f"/api/jobs/{second['id']}/assignment", json=dict(fields, expected_version=second["version"]))
    assert result.status_code == 409
    assert "conflict" in result.json()["detail"].lower()


def test_boundary_conflict_self_reschedule_and_disjoint_date(client):
    a, b = approved_job(client), approved_job(client)
    fields = assignment_fields(client)
    fields["end_date"] = (date.fromisoformat(fields["start_date"]) + timedelta(days=2)).isoformat()
    result = client.put(f"/api/jobs/{a['id']}/assignment", json=dict(fields, expected_version=a["version"]))
    assert result.status_code == 200
    a = result.json()
    assert client.put(f"/api/jobs/{a['id']}/assignment", json=dict(fields, expected_version=a["version"])).status_code == 200
    fields["start_date"] = fields["end_date"]
    assert client.put(f"/api/jobs/{b['id']}/assignment", json=dict(fields, expected_version=b["version"])).status_code == 409
    fields["start_date"] = fields["end_date"] = (date.fromisoformat(fields["end_date"]) + timedelta(days=1)).isoformat()
    assert client.put(f"/api/jobs/{b['id']}/assignment", json=dict(fields, expected_version=b["version"])).status_code == 200


def test_scheduling_prerequisites_and_foreign_resources(client, other_client):
    job = new_job(client)
    fields = assignment_fields(client)
    assert client.put(f"/api/jobs/{job['id']}/assignment", json=dict(fields, expected_version=job["version"])).status_code == 409
    job = approved_job(client)
    fields["end_date"] = "2020-01-01"
    assert client.put(f"/api/jobs/{job['id']}/assignment", json=dict(fields, expected_version=job["version"])).status_code == 422
    fields = assignment_fields(client)
    fields["crew_id"] = other_client.get("/api/bootstrap").json()["crews"][0]["id"]
    assert client.put(f"/api/jobs/{job['id']}/assignment", json=dict(fields, expected_version=job["version"])).status_code == 404


def test_status_transitions_and_completed_job_immutability(client):
    job = new_job(client)
    path = f"/api/jobs/{job['id']}"
    assert client.post(path+"/status", json={"expected_version":job["version"], "status":"completed"}).status_code == 409
    job = approved_job(client)
    path = f"/api/jobs/{job['id']}"
    fields = assignment_fields(client)
    job = client.put(path+"/assignment", json=dict(fields, expected_version=job["version"])).json()
    assert client.post(path+"/status", json={"expected_version":job["version"], "status":"completed"}).status_code == 409
    for status in ("in_progress", "completed"):
        result = client.post(path+"/status", json={"expected_version":job["version"],"status":status})
        assert result.status_code == 200
        job = result.json()
    assert client.put(path+"/assignment", json=dict(fields, expected_version=job["version"])).status_code == 409


def test_concurrent_reservation_has_one_winner(client, app):
    from app.scheduling import assign_job
    from app.schemas import AssignmentInput
    from app.db import transaction
    from app.models import Job, Assignment, ActivityEvent
    from app.errors import DomainError
    from sqlalchemy import select
    jobs = [approved_job(client), approved_job(client)]
    fields = assignment_fields(client)
    with transaction(app.state.engine) as s:
        ws = s.get(Job, jobs[0]["id"]).workspace_id
    barrier = Barrier(2)
    def reserve(job):
        barrier.wait(timeout=5)
        try:
            with transaction(app.state.engine, write=True) as s:
                assign_job(s, ws, job["id"], AssignmentInput(**fields, expected_version=job["version"]))
            return 200
        except DomainError as exc:
            return exc.status
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(reserve, jobs)) == [200, 409]
    with transaction(app.state.engine) as s:
        ids = [j["id"] for j in jobs]
        assert len(s.scalars(select(Assignment).where(Assignment.job_id.in_(ids))).all()) == 1
        assert len(s.scalars(select(ActivityEvent).where(ActivityEvent.job_id.in_(ids), ActivityEvent.kind=="schedule")).all()) == 1
