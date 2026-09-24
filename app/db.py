from contextlib import contextmanager
from pathlib import Path
from sqlalchemy import create_engine, event, inspect, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from .models import Base, SchemaVersion

WRITE_LOCK = 46092401


def make_engine(url):
    parsed = make_url(url)
    if parsed.get_backend_name() in {"postgresql", "postgres"}:
        return create_engine(parsed.set(drivername="postgresql+psycopg"), pool_pre_ping=True,
                             pool_size=5, max_overflow=0, connect_args={"connect_timeout": 15})
    if parsed.get_backend_name() != "sqlite":
        raise RuntimeError("Supported databases are SQLite and PostgreSQL.")
    if parsed.database and parsed.database != ":memory:":
        Path(parsed.database).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url, connect_args={"check_same_thread": False, "timeout": 10})

    @event.listens_for(engine, "connect")
    def configure(dbapi_connection, _):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")
        dbapi_connection.execute("PRAGMA busy_timeout=10000")
    return engine


def initialize(engine):
    with transaction(engine, write=True) as session:
        tables = inspect(session.connection()).get_table_names()
        if "schema_version" in tables:
            versions = session.scalars(select(SchemaVersion.version)).all()
            if versions != [1]:
                raise RuntimeError("Unsupported database schema. Back up the database and use a compatible app version.")
        elif tables:
            raise RuntimeError("Unrecognized database schema; refusing to modify existing tables.")
        else:
            Base.metadata.create_all(session.connection())
            session.add(SchemaVersion(id=1, version=1))


@contextmanager
def transaction(engine, write=False):
    with Session(engine, expire_on_commit=False) as session:
        try:
            if write:
                if engine.dialect.name == "sqlite":
                    session.execute(text("BEGIN IMMEDIATE"))
                else:
                    # Serialize demo writes before reading versions or reservations.
                    # The database releases this lock on commit/rollback, including
                    # across overlapping deployments and separate app instances.
                    session.execute(text("SET LOCAL lock_timeout = '10s'"))
                    session.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": WRITE_LOCK})
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
