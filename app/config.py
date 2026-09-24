import os
from dataclasses import dataclass


@dataclass
class Settings:
    database_url: str
    origin: str
    cookie_secure: bool

    @classmethod
    def load(cls, database_url=None, origin=None):
        return cls(database_url or os.getenv("DATABASE_URL", "sqlite:///data/frank.db"),
                   (origin or os.getenv("APP_ORIGIN", "http://127.0.0.1:8000")).rstrip("/"),
                   os.getenv("COOKIE_SECURE", "false").lower() == "true")
