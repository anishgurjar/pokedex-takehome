"""Pytest loads `.env` and `.env.test` before the app (see `.env.test`)."""

import os
import uuid
from collections.abc import Generator
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine.url import make_url

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PROJECT_ROOT / ".env.test", override=True)

# Canonical test template URL (directory is used for per-test ephemeral SQLite files).
_TEST_DATABASE_URL_TEMPLATE = os.environ.get(
    "DATABASE_URL", "sqlite:///./data/poketracker_test.db"
)

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402


def _per_test_sqlite_url_and_path() -> tuple[str, Path]:
    """Create a unique DB file next to the directory from `.env.test` DATABASE_URL."""
    template = make_url(_TEST_DATABASE_URL_TEMPLATE)
    if template.drivername != "sqlite":
        msg = "pytest expects DATABASE_URL in .env.test to use sqlite"
        raise RuntimeError(msg)
    db_part = template.database
    if not db_part or db_part == ":memory:":
        test_dir = PROJECT_ROOT / "data" / "pytest_scratch"
    else:
        resolved = (PROJECT_ROOT / db_part).resolve()
        test_dir = resolved.parent
    test_dir.mkdir(parents=True, exist_ok=True)
    path = test_dir / f"pytest_{uuid.uuid4().hex}.db"
    url = f"sqlite:///{path.resolve()}"
    return url, path


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Ephemeral SQLite file per test; schema from Alembic migrations."""
    url, path = _per_test_sqlite_url_and_path()
    os.environ["DATABASE_URL"] = url

    import app.database as db

    db.configure_engine()

    cfg = Config(str(PROJECT_ROOT / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")

    session = db.SessionLocal()
    try:
        yield session
    finally:
        session.close()
        db.engine.dispose()
        path.unlink(missing_ok=True)
        os.environ["DATABASE_URL"] = _TEST_DATABASE_URL_TEMPLATE


@pytest.fixture
def client(db_session: Session):
    """FastAPI client using the migrated test database."""
    from app.deps import get_db
    from app.main import app
    from fastapi.testclient import TestClient

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_pokemon(db_session):
    """Insert a few Pokémon species for testing."""
    from app.models import Pokemon

    pokemon_data = [
        Pokemon(
            id=1,
            name="Bulbasaur",
            type1="Grass",
            type2="Poison",
            generation=1,
            is_legendary=False,
            is_mythical=False,
            is_baby=False,
            capture_rate=45,
            evolution_chain_id=1,
        ),
        Pokemon(
            id=4,
            name="Charmander",
            type1="Fire",
            type2=None,
            generation=1,
            is_legendary=False,
            is_mythical=False,
            is_baby=False,
            capture_rate=45,
            evolution_chain_id=2,
        ),
        Pokemon(
            id=7,
            name="Squirtle",
            type1="Water",
            type2=None,
            generation=1,
            is_legendary=False,
            is_mythical=False,
            is_baby=False,
            capture_rate=45,
            evolution_chain_id=3,
        ),
        Pokemon(
            id=25,
            name="Pikachu",
            type1="Electric",
            type2=None,
            generation=1,
            is_legendary=False,
            is_mythical=False,
            is_baby=False,
            capture_rate=190,
            evolution_chain_id=10,
        ),
        Pokemon(
            id=144,
            name="Articuno",
            type1="Ice",
            type2="Flying",
            generation=1,
            is_legendary=True,
            is_mythical=False,
            is_baby=False,
            capture_rate=3,
            evolution_chain_id=73,
        ),
        Pokemon(
            id=150,
            name="Mewtwo",
            type1="Psychic",
            type2=None,
            generation=1,
            is_legendary=True,
            is_mythical=False,
            is_baby=False,
            capture_rate=3,
            evolution_chain_id=77,
        ),
        Pokemon(
            id=151,
            name="Mew",
            type1="Psychic",
            type2=None,
            generation=1,
            is_legendary=False,
            is_mythical=True,
            is_baby=False,
            capture_rate=45,
            evolution_chain_id=78,
        ),
        Pokemon(
            id=152,
            name="Chikorita",
            type1="Grass",
            type2=None,
            generation=2,
            is_legendary=False,
            is_mythical=False,
            is_baby=False,
            capture_rate=45,
            evolution_chain_id=79,
        ),
        Pokemon(
            id=175,
            name="Togepi",
            type1="Fairy",
            type2=None,
            generation=2,
            is_legendary=False,
            is_mythical=False,
            is_baby=True,
            capture_rate=190,
            evolution_chain_id=87,
        ),
    ]

    for p in pokemon_data:
        db_session.add(p)
    db_session.commit()
    return pokemon_data


@pytest.fixture
def sample_ranger(client):
    """Create a sample ranger and return the response data."""
    response = client.post(
        "/rangers",
        json={
            "name": "Ranger Ash",
            "email": "ash@pokemon-institute.org",
            "specialization": "Electric",
        },
    )
    return response.json()


@pytest.fixture
def second_ranger(client):
    """Create a second ranger for peer confirmation tests."""
    response = client.post(
        "/rangers",
        json={
            "name": "Ranger Gary",
            "email": "gary@pokemon-institute.org",
            "specialization": "Water",
        },
    )
    return response.json()


@pytest.fixture
def sample_trainer(client):
    """Create a sample trainer and return the response data."""
    response = client.post(
        "/trainers",
        json={
            "name": "Trainer Red",
            "email": "red@pokemon-league.org",
        },
    )
    return response.json()


@pytest.fixture
def sample_sighting(client, sample_pokemon, sample_ranger):
    """Create a sample sighting and return the response data."""
    response = client.post(
        "/sightings",
        json={
            "pokemon_id": 25,
            "region": "Kanto",
            "route": "Route 1",
            "date": "2025-06-15T10:30:00",
            "weather": "sunny",
            "time_of_day": "morning",
            "height": 0.4,
            "weight": 6.0,
            "is_shiny": False,
            "notes": "Spotted near Viridian City",
        },
        headers={"X-User-ID": sample_ranger["id"]},
    )
    return response.json()
