# PokéTracker API

FastAPI + SQLite + SQLAlchemy. Schema is managed with **Alembic** (the app does not run `create_all()` at startup).

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
- **Beekeeper / SQLite GUIs:** open the **absolute** path to `./data/poketracker.db` on disk. Relative URLs like `sqlite:///./data/...` can resolve to the wrong folder from the GUI.

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

Pytest loads `.env` then `.env.test` and migrates ephemeral `data/pytest_*.db` files per test.

```bash
uv run pytest
```

## Docker (optional)

```bash
docker compose up --build
```

Compose bind-mounts **`./data`** to `/data` in the container. The SQLite file on your machine is `./data/poketracker.db`.
