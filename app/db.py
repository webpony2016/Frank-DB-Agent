from contextlib import contextmanager
from pathlib import Path
from sqlalchemy import create_engine, event, inspect, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from .models import Base, SchemaVersion


def make_engine(url):
    parsed = make_url(url)
    if parsed.get_backend_name() != "sqlite":
        raise RuntimeError("This local demo requires SQLite. PostgreSQL locking/migrations are not yet verified.")
    if parsed.database and parsed.database != ":memory:":
        Path(parsed.database).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url, connect_args={"check_same_thread": False, "timeout": 10})

    @event.listens_for(engine, "connect")
    def configure(dbapi_connection, _):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")
        dbapi_connection.execute("PRAGMA busy_timeout=10000")
    return engine


def initialize(engine):
    tables = inspect(engine).get_table_names()
    with Session(engine) as session:
        if "schema_version" in tables:
            versions = session.scalars(select(SchemaVersion.version)).all()
            if versions != [1]:
                raise RuntimeError("Unsupported database schema. Back up the database and use a compatible app version.")
        elif tables:
            raise RuntimeError("Unrecognized database schema; refusing to modify existing tables.")
        else:
            Base.metadata.create_all(engine)
            session.add(SchemaVersion(id=1, version=1))
            session.commit()


@contextmanager
def transaction(engine, write=False):
    with Session(engine, expire_on_commit=False) as session:
        try:
            if write:
                session.execute(text("BEGIN IMMEDIATE"))
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
