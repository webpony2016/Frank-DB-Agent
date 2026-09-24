import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def app(tmp_path):
    from app.main import create_app
    return create_app(f"sqlite:///{tmp_path / 'test.db'}", "http://testserver")


@pytest.fixture
def client(app):
    with TestClient(app, headers={"Origin": "http://testserver"}) as c:
        c.get("/api/bootstrap")
        yield c


@pytest.fixture
def other_client(app):
    with TestClient(app, headers={"Origin": "http://testserver"}) as c:
        c.get("/api/bootstrap")
        yield c


def new_job(client):
    inquiry = next(i for i in client.get("/api/bootstrap").json()["inquiries"] if not i["job_id"])
    response = client.post(f"/api/inquiries/{inquiry['id']}/brief")
    assert response.status_code == 200, response.text
    brief = response.json()["brief"]
    brief.pop("missing_information", None)
    response = client.post(f"/api/inquiries/{inquiry['id']}/job", json=brief)
    assert response.status_code == 201, response.text
    return response.json()



def save_quote(client, job, price="125.55"):
    response = client.post(f"/api/jobs/{job['id']}/quotes", json={"expected_version": job["version"],
        "lines": [{"description": "Illustrative mobilization", "quantity": "2", "unit_price": price}]})
    assert response.status_code == 200, response.text
    return response.json()


def approved_job(client):
    job = save_quote(client, new_job(client))
    response = client.post(f"/api/jobs/{job['id']}/quotes/{job['quotes'][-1]['id']}/approve",
                           json={"expected_version": job["version"]})
    assert response.status_code == 200, response.text
    return response.json()



def assignment_fields(client):
    from datetime import date, timedelta
    boot = client.get("/api/bootstrap").json()
    day = (date.fromisoformat(boot["business_date"]) + timedelta(days=90)).isoformat()
    return dict(crew_id=boot["crews"][0]["id"], equipment_id=boot["equipment"][0]["id"], start_date=day, end_date=day)
