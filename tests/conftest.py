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

