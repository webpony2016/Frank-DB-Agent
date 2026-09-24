from datetime import datetime, date
from zoneinfo import ZoneInfo


def test_workspace_seeds_once_and_is_isolated(client, other_client):
    one = client.get("/api/bootstrap").json()
    again = client.get("/api/bootstrap").json()
    two = other_client.get("/api/bootstrap").json()
    assert one["mode"] == "sample"
    assert one["jobs"] and len(one["inquiries"]) == 3
    assert [j["id"] for j in one["jobs"]] == [j["id"] for j in again["jobs"]]
    assert {j["id"] for j in one["jobs"]}.isdisjoint(j["id"] for j in two["jobs"])
    assert client.get("/api/bootstrap").headers["cache-control"] == "no-store"
    assert one["metrics"]["active_jobs"] == 5


def test_forged_cookie_gets_new_workspace(client):
    before = client.get("/api/bootstrap").json()
    client.cookies.clear()
    client.cookies.set("frank_workspace", "made-up-token")
    response = client.get("/api/bootstrap")
    assert response.json()["jobs"][0]["id"] != before["jobs"][0]["id"]
    assert "HttpOnly" in response.headers["set-cookie"]
    assert "samesite=lax" in response.headers["set-cookie"].lower()


def test_seed_date_is_injected_and_toronto_date_respected(client):
    from app.seed import business_date
    instant = datetime.fromisoformat("2026-09-24T02:30:00+00:00")
    assert business_date(instant) == date(2026, 9, 23)
    boot = client.get("/api/bootstrap").json()
    assert boot["business_date"] == datetime.now(ZoneInfo("America/Toronto")).date().isoformat()
    assert any(a["start_date"] == boot["business_date"] for a in boot["assignments"])


def test_unknown_schema_is_not_overwritten(tmp_path):
    import sqlite3
    from app.main import create_app
    from fastapi.testclient import TestClient
    import pytest
    path = tmp_path / "future.db"
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE schema_version (id INTEGER PRIMARY KEY, version INTEGER NOT NULL)")
        conn.execute("INSERT INTO schema_version VALUES (1, 99)")
    with pytest.raises(RuntimeError, match="schema"):
        with TestClient(create_app(f"sqlite:///{path}", "http://testserver")):
            pass
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT version FROM schema_version").fetchone()[0] == 99
