import pytest
from conftest import new_job, save_quote, approved_job


def test_old_quote_cannot_be_approved(client):
    job = save_quote(client, new_job(client))
    old = job["quotes"][-1]["id"]
    job = save_quote(client, job, "99.99")
    assert client.post(f"/api/jobs/{job['id']}/quotes/{old}/approve", json={"expected_version": job["version"]}).status_code == 409
    assert job["quotes"][-1]["total"] == "199.98"
    current = job["quotes"][-1]["id"]
    response = client.post(f"/api/jobs/{job['id']}/quotes/{current}/approve", json={"expected_version": job["version"]})
    assert response.status_code == 200
    assert response.json()["status"] == "quoted"


def test_approved_revision_is_frozen_and_new_draft_requires_approval(client):
    job = approved_job(client)
    old = job["quotes"][-1]
    revised = save_quote(client, job, "20.00")
    assert revised["status"] == "draft"
    assert revised["quotes"][0] == old
    assert revised["quotes"][-1]["state"] == "draft"
    response = client.post(f"/api/jobs/{job['id']}/quotes", json={"expected_version": job["version"], "lines": [{"description": "x", "quantity": "1", "unit_price": "10"}]})
    assert response.status_code == 409


@pytest.mark.parametrize("field,value", [
    ("quantity","NaN"), ("unit_price","Infinity"), ("quantity","-1"), ("unit_price","-0.01"),
    ("quantity","0.0001"), ("unit_price","1.001"), ("quantity","100001"), ("unit_price","1000001")
])
def test_invalid_money_has_no_side_effect(client, field, value):
    job = new_job(client)
    line = {"description":"Illustrative service","quantity":"1","unit_price":"10.00"}
    line[field] = value
    response = client.post(f"/api/jobs/{job['id']}/quotes", json={"expected_version":job["version"],"lines":[line]})
    assert response.status_code == 422, response.text
    assert client.get(f"/api/jobs/{job['id']}").json() == job


@pytest.mark.parametrize("lines,expected", [
    ([{"description":"x","quantity":"0.333","unit_price":"10.00"}], "3.33"),
    ([{"description":"x","quantity":"0.005","unit_price":"1.00"}]*2, "0.02"),
    ([{"description":"x","quantity":"0","unit_price":"1.00"}], "0.00")
])
def test_rounding_is_per_line(client, lines, expected):
    job = new_job(client)
    result = client.post(f"/api/jobs/{job['id']}/quotes", json={"expected_version":job["version"],"lines":lines})
    assert result.status_code == 200
    assert result.json()["quotes"][-1]["total"] == expected


@pytest.mark.parametrize("lines", [[], [{"description":"x"*301,"quantity":"1","unit_price":"1"}],
    [{"description":"x","quantity":"100000","unit_price":"1000000"}]])
def test_line_bounds_and_total_overflow(client, lines):
    job = new_job(client)
    result = client.post(f"/api/jobs/{job['id']}/quotes", json={"expected_version":job["version"],"lines":lines})
    assert result.status_code == 422
    assert not client.get(f"/api/jobs/{job['id']}").json()["quotes"]


def test_quote_scope_and_scheduled_immutability(client, other_client):
    a, b = save_quote(client, new_job(client)), save_quote(client, new_job(client))
    assert client.post(f"/api/jobs/{a['id']}/quotes/{b['quotes'][-1]['id']}/approve", json={"expected_version":a["version"]}).status_code == 404
    assert other_client.post(f"/api/jobs/{a['id']}/quotes/{a['quotes'][-1]['id']}/approve", json={"expected_version":a["version"]}).status_code == 404
    for status in ("scheduled","completed"):
        job = next(j for j in client.get("/api/bootstrap").json()["jobs"] if j["status"] == status)
        response = client.post(f"/api/jobs/{job['id']}/quotes", json={"expected_version":job["version"],"lines":[{"description":"x","quantity":"1","unit_price":"1"}]})
        assert response.status_code == 409
