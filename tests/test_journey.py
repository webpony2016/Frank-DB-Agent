from fastapi.testclient import TestClient
from conftest import approved_job, assignment_fields, new_job


def test_complete_journey_survives_new_app_instance(client, app):
    from app.main import create_app
    job = approved_job(client)
    path = f"/api/jobs/{job['id']}"
    job = client.put(path+"/assignment", json=dict(assignment_fields(client), expected_version=job["version"])).json()
    for status in ("in_progress", "completed"):
        response = client.post(path+"/status", json={"expected_version":job["version"],"status":status})
        assert response.status_code == 200
        job = response.json()
    job = client.post(path+"/drafts", json={"expected_version":job["version"]}).json()
    cookies = dict(client.cookies)
    replacement = create_app(app.state.settings.database_url, "http://testserver")
    with TestClient(replacement, headers={"Origin":"http://testserver"}, cookies=cookies) as restarted:
        saved = restarted.get(path).json()
        assert saved["status"] == "completed"
        assert saved["quotes"][-1]["total"] == "251.10"
        assert saved["drafts"] == job["drafts"]
        assert saved["assignment"] == job["assignment"]


def test_reset_only_changes_current_workspace(client, other_client):
    job = new_job(client)
    others = other_client.get("/api/bootstrap").json()["jobs"]
    assert client.post("/api/reset", json={"confirm":False}).status_code == 422
    result = client.post("/api/reset", json={"confirm":True})
    assert result.status_code == 200
    assert len(result.json()["jobs"]) == 6
    assert client.get(f"/api/jobs/{job['id']}").status_code == 404
    assert other_client.get("/api/bootstrap").json()["jobs"] == others


def test_mutation_origin_and_body_bounds(client):
    assert client.post("/api/reset", json={"confirm":True}, headers={"Origin":"https://invalid.example"}).status_code == 403
    client.headers.pop("origin", None)
    assert client.post("/api/reset", json={"confirm":True}).status_code == 403
    assert client.post("/api/reset", content="x"*65537, headers={"Origin":"http://testserver"}).status_code == 413


def test_all_job_mutations_hide_foreign_ids(client, other_client):
    job = approved_job(client)
    version = {"expected_version":job["version"]}
    actions = [
        ("POST","quotes",dict(version,lines=[{"description":"x","quantity":"1","unit_price":"1"}])),
        ("POST","quotes/"+job["quotes"][-1]["id"]+"/approve",version),
        ("PUT","assignment",dict(assignment_fields(client),**version)),
        ("POST","status",dict(version,status="completed")),
        ("POST","notes",dict(version,text="x")),
        ("POST","drafts",version),
        ("POST","integration-previews",dict(version,connector="crm")),
    ]
    for method,suffix,body in actions:
        assert other_client.request(method,f"/api/jobs/{job['id']}/"+suffix,json=body).status_code == 404


def test_stale_assignment_leaves_saved_booking_unchanged(client):
    job = approved_job(client)
    fields = assignment_fields(client)
    path=f"/api/jobs/{job['id']}"
    response=client.put(path+"/assignment",json=dict(fields,expected_version=job["version"]))
    assert response.status_code==200
    saved=response.json()
    assert client.put(path+"/assignment",json=dict(fields,expected_version=job["version"])).status_code==409
    assert client.get(path).json()==saved


def test_completed_future_job_is_not_upcoming(client):
    job=approved_job(client)
    fields=assignment_fields(client)
    path=f"/api/jobs/{job['id']}"
    original=client.get("/api/bootstrap").json()["metrics"]["upcoming"]
    job=client.put(path+"/assignment",json=dict(fields,expected_version=job["version"])).json()
    for status in ("in_progress","completed"):
        job=client.post(path+"/status",json={"expected_version":job["version"],"status":status}).json()
    assert client.get("/api/bootstrap").json()["metrics"]["upcoming"]==original
