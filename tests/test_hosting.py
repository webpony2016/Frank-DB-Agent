from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy import select, func, BigInteger
from app.db import transaction, make_engine
from app.main import create_app
from app.models import Workspace, Quote, QuoteLine, ActivityEvent


def test_expired_token_cannot_read_and_bootstrap_replaces_it(client, app):
    before = client.get('/api/bootstrap').json()
    with transaction(app.state.engine, write=True) as session:
        workspace = session.scalar(select(Workspace))
        workspace.created_at = (datetime.now(timezone.utc) - timedelta(days=8)).isoformat()
    assert client.get('/api/jobs/' + before['jobs'][0]['id']).status_code == 401
    after = client.get('/api/bootstrap').json()
    assert after['jobs'][0]['id'] != before['jobs'][0]['id']
    with transaction(app.state.engine) as session:
        assert session.scalar(select(func.count()).select_from(Workspace)) == 1


def test_workspace_capacity_preserves_existing_visitors(client, app):
    app.state.settings.max_workspaces = 1
    with TestClient(app, headers={'Origin': 'http://testserver'}) as visitor:
        assert visitor.get('/api/bootstrap').status_code == 429
    assert client.get('/api/bootstrap').status_code == 200


def test_workspace_event_limit_is_atomic(client, app):
    boot = client.get('/api/bootstrap').json()
    job = client.get('/api/jobs/' + boot['jobs'][0]['id']).json()
    with transaction(app.state.engine) as session:
        app.state.settings.max_events = session.scalar(select(func.count()).select_from(ActivityEvent)) + 1
    path = '/api/jobs/' + job['id']
    first = client.post(path + '/notes', json={'expected_version': job['version'], 'text': 'One allowed note'})
    assert first.status_code == 200
    second = client.post(path + '/notes', json={'expected_version': first.json()['version'], 'text': 'Over quota'})
    assert second.status_code == 429
    assert client.get(path).json() == first.json()
    assert client.post('/api/reset', json={'confirm': True}).status_code == 200


def test_https_configuration_enforces_secure_cookie(tmp_path, monkeypatch):
    monkeypatch.setenv('COOKIE_SECURE', 'false')
    application = create_app(f'sqlite:///{tmp_path / "https.db"}', 'https://demo.example')
    with TestClient(application, base_url='https://demo.example') as visitor:
        response = visitor.get('/api/bootstrap')
        assert '; Secure' in response.headers['set-cookie']
        assert response.headers['strict-transport-security'] == 'max-age=31536000'


def test_hosted_configuration_refuses_ephemeral_sqlite(monkeypatch):
    import pytest
    monkeypatch.setenv('RENDER', 'true')
    monkeypatch.delenv('DATABASE_URL', raising=False)
    with pytest.raises(RuntimeError, match='PostgreSQL'):
        create_app()


def test_quote_cents_support_postgres_int64():
    assert isinstance(Quote.__table__.c.total_cents.type, BigInteger)
    assert isinstance(QuoteLine.__table__.c.total_cents.type, BigInteger)


def test_postgres_url_uses_psycopg_without_connecting():
    engine = make_engine('postgresql://example:example@localhost/frank')
    assert engine.dialect.name == 'postgresql'
    assert engine.dialect.driver == 'psycopg'
    engine.dispose()


def test_rate_limit_has_retry_header_and_does_not_seed(tmp_path):
    application = create_app(f'sqlite:///{tmp_path / "rate.db"}', 'http://testserver')
    application.state.settings.requests_per_minute = 2
    with TestClient(application) as visitor:
        assert visitor.get('/api/bootstrap').status_code == 200
        assert visitor.get('/api/bootstrap').status_code == 200
        response = visitor.get('/api/bootstrap')
        assert response.status_code == 429
        assert response.headers['retry-after'] == '60'
        assert visitor.get('/health').status_code == 200


def test_large_valid_quote_persists_without_int32_overflow(client):
    from conftest import new_job
    job = new_job(client)
    result = client.post('/api/jobs/' + job['id'] + '/quotes', json={
        'expected_version': job['version'],
        'lines': [{'description': 'Illustrative maximum', 'quantity': '100', 'unit_price': '1000000.00'}],
    })
    assert result.status_code == 200
    assert result.json()['quotes'][-1]['total'] == '100000000.00'
