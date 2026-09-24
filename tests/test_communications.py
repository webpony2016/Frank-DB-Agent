import socket
import pytest
from conftest import new_job, approved_job, assignment_fields


def test_customer_draft_uses_saved_facts_and_can_be_edited(client):
    job = new_job(client)
    path = f"/api/jobs/{job['id']}"
    response = client.post(path+"/drafts", json={"expected_version":job["version"]})
    assert response.status_code == 200
    job = response.json()
    draft = job["drafts"][-1]
    assert job["site"] in draft["body"]
    assert "pending" in draft["body"].lower()
    assert draft["mode"] == "sample" and draft["state"] == "draft"
    response = client.put(path+f"/drafts/{draft['id']}", json={"expected_version":job["version"],"subject":"Reviewed update","body":"Ready for operator review."})
    assert response.status_code == 200
    assert client.get(path).json()["drafts"][-1]["body"] == "Ready for operator review."


def test_html_notes_are_stored_as_text_and_bounded(client):
    job = new_job(client)
    payload = "<img src=x onerror=alert(1)>"
    path = f"/api/jobs/{job['id']}"
    response = client.post(path+"/notes", json={"expected_version":job["version"],"text":payload})
    assert response.status_code == 200
    job = response.json()
    assert job["activity"][-1]["text"] == payload
    for value in (" ", "x"*4001):
        assert client.post(path+"/notes", json={"expected_version":job["version"],"text":value}).status_code == 422


@pytest.mark.parametrize("connector", ["quickbooks", "email_calendar", "crm"])
def test_previews_are_local_and_fact_based(client, monkeypatch, connector):
    job = approved_job(client)
    job = client.put(f"/api/jobs/{job['id']}/assignment", json=dict(assignment_fields(client), expected_version=job["version"])).json()
    def offline(*args, **kwargs):
        raise AssertionError("A preview must never connect to an external server")
    monkeypatch.setattr(socket, "create_connection", offline)
    response = client.post(f"/api/jobs/{job['id']}/integration-previews",
        json={"expected_version":job["version"],"connector":connector})
    assert response.status_code == 200
    preview = response.json()["preview"]
    assert preview["mode"] == "sample" and preview["sent"] is False and preview["connected"] is False
    assert preview["payload"]["job_id"] == job["id"]
    listing = client.get("/api/integrations").json()
    assert all(c["connected"] is False for c in listing["connectors"])
    assert listing["history"][-1]["id"] == preview["id"]
    if connector == "quickbooks":
        assert preview["payload"]["amount_cad"] == "251.10"
    if connector == "email_calendar":
        assert preview["payload"]["start_date"] == job["assignment"]["start_date"]


def test_missing_integration_prerequisites_are_explained(client):
    job = new_job(client)
    for connector in ("quickbooks", "email_calendar"):
        response = client.post(f"/api/jobs/{job['id']}/integration-previews", json={"expected_version":job["version"],"connector":connector})
        assert response.status_code == 409
    assert client.post(f"/api/jobs/{job['id']}/integration-previews", json={"expected_version":job["version"],"connector":"unknown"}).status_code == 422


def test_foreign_draft_is_inaccessible(client, other_client):
    a, b = new_job(client), new_job(other_client)
    result = client.post(f"/api/jobs/{a['id']}/drafts", json={"expected_version":a["version"]})
    assert result.status_code == 200
    draft = result.json()["drafts"][-1]
    assert other_client.put(f"/api/jobs/{b['id']}/drafts/{draft['id']}",
        json={"expected_version":b["version"],"subject":"x","body":"x"}).status_code == 404
