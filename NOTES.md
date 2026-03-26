Cleaned up the repo, wired Ruff + pre-commit, and got tests passing. Added `.env` / `.env.example`, Alembic (no runtime `create_all`), and pytest setup that loads `.env` + `.env.test` and runs migrations on ephemeral SQLite files per test so dev vs test data stay separate and future DB work is less painful.

The seed script was out of date: it imported non-existent top-level modules, read the wrong JSON file, used old model field names (`species_name`, `pokemon_name`, `confirmed`), bypassed Alembic with `create_all`, and could not import `app` when run as `python scripts/seed.py` until the project was packaged in `pyproject.toml`. It now runs migrations first, loads `data/pokedex_entries.json`, inserts with the current schema, and optional `SEED_SIGHTING_COUNT` for faster tests.

**`chore/refactor-endpoints` (unified users + API cleanup + auth):**

- **One user row, role-specific profiles:** `app_users` holds shared identity (email, display name, status, id); `trainers` / `rangers` are thin FK extensions so we are not copying user fields per role and sightings still reference rangers cleanly.
- **Roles in the DB:** `role` and `status` use check constraints so the database enforces the same trainer/ranger and active/disabled rules the API expects instead of only app-layer validation.
- **Indexes:** `idx_app_users_email_norm` speeds “email already registered” checks; `idx_app_users_role_name` on `(role, display_name_normalized)` supports lookup/listing by normalized name within a role; unique `display_name_normalized` gives a single canonical handle per display identity.
- **Sightings auth:** Replaced spoofable identity headers with signed bearer JWTs so the server verifies who is calling, not whatever id the client sends.

**Sightings list + DB hardening (feature 1 + defense in depth):**

- **`GET /sightings`:** Typed query params (Pydantic) for filters, cursor-based pagination on `date DESC, id DESC` (stable ordering), and `total_count` so clients can page without guessing how many rows match.
- **`SightingRepository`:** Centralizes query building with an allowlisted filter map and parameterized SQLAlchemy predicates so adding/removing filters is one place and we avoid dynamic SQL from user input.
- **Indexes on `sightings`:** Composite indexes aligned to common filter + sort patterns so large regional lists stay usable as data grows.
- **Check constraints + `EmailStr`:** SQLite `CHECK` rules mirror domain enums and non-empty/trimmed text for sightings, users, rangers, and Pokémon reference rows; registration emails use Pydantic `EmailStr` plus `email-validator` so invalid addresses fail at the API before they hit the DB, while constraints still protect against bypasses (raw SQL, bugs, future code paths).
