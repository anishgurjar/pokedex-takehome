# PokéTracker API

Backend for the **Pokémon Research Institute** field-research Pokédex: rangers log sightings, run campaigns, and pull regional summaries. Built as a **FastAPI** service over **SQLite** with **SQLAlchemy 2** and **Alembic** (the app does **not** call `create_all()` at startup).

**Stack:** Python 3.12 · FastAPI · SQLite · SQLAlchemy · Alembic · pytest · uv · Ruff

Design notes, prioritization, and trade-offs (including pagination and auth choices) live in **[NOTES.md](./NOTES.md)**.

---

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

## Quick start

```bash
uv sync --group dev
cp .env.example .env
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

- **Config:** `app/config.py` loads `.env`. Default `DATABASE_URL` is `sqlite:///./data/poketracker.db` (see `.env.example`).
- **Beekeeper / SQLite GUIs:** open the **absolute** path to `./data/poketracker.db` on disk. Relative URLs like `sqlite:///./data/...` can resolve to the wrong working directory from the GUI.

## Seed data

Populate species reference data and (optionally) a large volume of sightings:

```bash
uv run python scripts/seed.py
```

Set **`SEED_SIGHTING_COUNT`** (default `55000`) if you want fewer sightings for a quicker local load.

## API surface (high level)

Routers cover trainers, rangers, Pokédex reference data, sightings (list, CRUD, peer confirmation), research **campaigns** (lifecycle + summaries), and **regional** aggregates. Protected ranger actions expect **`Authorization: Bearer <JWT>`** signed with **`JWT_SECRET`** (see `app/auth.py` for claims; **`tests/conftest.py`** shows how tests mint tokens). **NOTES.md** explains how this differs from the original `X-User-ID` wording in the exercise brief.

## Migrations

**Apply all pending migrations**

```bash
uv run alembic upgrade head
```

**Change the schema** (edit `app/models.py`, then)

```bash
uv run alembic revision --autogenerate -m "short_description"
uv run alembic upgrade head
```

Review the new file under `alembic/versions/` before you commit.

**Existing DB with tables but no migration history** (one-time)

```bash
uv run alembic stamp head
```

**Autogenerate against a clean empty DB** (helps get a full diff)

```bash
rm -f /tmp/gen.db && DATABASE_URL=sqlite:////tmp/gen.db uv run alembic revision --autogenerate -m "short_description"
```

## Tests

Pytest loads `.env` then `.env.test` and migrates ephemeral `data/pytest_*.db` files per test session.

```bash
uv run pytest
```

Candidate-written scenarios for the take-home live in **`tests/test_candidate.py`**; the rest of **`tests/`** covers routers, repositories, and integration paths.

## Lint and format

Same rules as optional pre-commit hooks:

```bash
uv run ruff check --fix .
uv run ruff format .
```

Install hooks once per clone:

```bash
uv run pre-commit install
```

## Docker (optional)

```bash
docker compose up --build
```

Compose bind-mounts **`./data`** to `/data` in the container. The SQLite file on your machine is `./data/poketracker.db`.
