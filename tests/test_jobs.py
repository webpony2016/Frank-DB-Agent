from conftest import new_job
from sqlalchemy import select
from app.db import transaction
from app.models import Inquiry


def test_job_ids_do_not_bypass_workspace(client, other_client):
    job = new_job(client)
    assert other_client.get(f"/api/jobs/{job['id']}").status_code == 404


def test_conversion_is_idempotent(client):
    inquiry = next(i for i in client.get("/api/bootstrap").json()["inquiries"] if not i["job_id"])
    path = f"/api/inquiries/{inquiry['id']}"
    result = client.post(path + "/brief")
    assert result.status_code == 200
    assert result.json()["mode"] == "sample"
    brief = result.json()["brief"]
    brief.pop("missing_information", None)
    brief["site"] = "Fictional site reviewed by operator"
    first = client.post(path + "/job", json=brief)
    second = client.post(path + "/job", json=brief)
    assert (first.status_code, second.status_code) == (201, 200)
    assert first.json()["id"] == second.json()["id"]
    assert second.json()["site"] == brief["site"]


def test_bad_dates_and_foreign_customer_rejected(client, other_client):
    inquiry = client.get("/api/bootstrap").json()["inquiries"][0]
    path = f"/api/inquiries/{inquiry['id']}"
    assert other_client.post(path + "/brief").status_code == 404
    assert client.post(path + "/brief").status_code == 200
    brief = client.post(path + "/brief").json()["brief"]
    brief.pop("missing_information")
    brief["requested_end"] = "2020-01-01"
    assert client.post(path + "/job", json=brief).status_code == 422
    brief["requested_end"] = brief["requested_start"]
    brief["customer_id"] = other_client.get("/api/bootstrap").json()["customers"][0]["id"]
    assert client.post(path + "/job", json=brief).status_code == 404


def test_unknown_example_requests_manual_details(client, app):
    inquiry = client.get("/api/bootstrap").json()["inquiries"][0]
    with transaction(app.state.engine, write=True) as session:
        row = session.get(Inquiry, inquiry["id"])
        row.sample_key = "unrecognized"
    response = client.post(f"/api/inquiries/{inquiry['id']}/brief")
    assert response.status_code == 200
    assert response.json()["provenance"] == "manual-entry-required"
    assert response.json()["brief"]["site"] == ""
