import os
from dataclasses import dataclass
from sqlalchemy.engine import make_url


@dataclass
class Settings:
    database_url: str
    origin: str
    cookie_secure: bool
    max_workspaces: int = 100
    max_events: int = 200
    requests_per_minute: int = 120

    @classmethod
    def load(cls, database_url=None, origin=None):
        url = database_url or os.getenv("DATABASE_URL", "sqlite:///data/frank.db")
        app_origin = (origin or os.getenv("APP_ORIGIN") or os.getenv("RENDER_EXTERNAL_URL") or "http://127.0.0.1:8000").rstrip("/")
        if os.getenv("RENDER") == "true" and make_url(url).get_backend_name() not in {"postgresql", "postgres"}:
            raise RuntimeError("Render requires durable PostgreSQL; local SQLite is ephemeral.")
        return cls(url, app_origin, app_origin.startswith("https://") or os.getenv("COOKIE_SECURE", "false").lower() == "true")
