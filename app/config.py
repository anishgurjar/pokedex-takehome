"""Application configuration from environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
# Local dev: load `.env` (not checked in). Pytest loads `.env` + `.env.test` separately.
load_dotenv(_PROJECT_ROOT / ".env", override=False)


def get_database_url() -> str:
    """SQLite URL for SQLAlchemy. Set `DATABASE_URL` in `.env`."""
    return os.environ.get("DATABASE_URL", "sqlite:///./data/poketracker.db")
