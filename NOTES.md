## Prioritization

Since the prompt explicitly allows prioritizing depth over breadth and beacuse I had limited time, I focused on the **initial seed fix** plus **Features 1–4** (sighting filters/list, research campaigns, peer confirmation, regional research summary).

**Why these four:** They form a coherent “field research” story—rangers need to **find** sightings at scale (Feature 1), **organize** work under campaigns with enforceable lifecycle rules (Feature 2), **trust** data via peer confirmation (Feature 3), and **report** region-level aggregates for leadership, including the performance angle called out in Feature 4. That line of work exercises SQLAlchemy, constraints, API design, and heavier read paths in one thread.

**What I deprioritized and why:** **Feature 5** (rarity / anomaly analysis) needs a defensible anomaly definition and extra narrative in this file; I did not want to ship a vague heuristic under time pressure. **Feature 6** (leaderboard) largely composes rankings I already touch in Feature 4’s “top rangers” slice, so it felt like incremental product polish rather than new core domain. **Feature 7** (trainer catch tracking) is a separate user journey from ranger research; doing it justice would mean more models, auth rules, and tests without deepening the research pipeline I chose to finish.

## Tooling and structure (why the extra glue)

- **Alembic migrations:** The assessment is database-heavy (sightings at scale, campaigns, confirmation metadata). I wanted the schema to be explicit, reviewable, and reproducible—no silent `create_all()` drift between environments or tests.
- **Layering / DDD-style layout:** Domain packages (`app/domain/…`), repositories, and services keep lifecycle and confirmation rules out of routers so invariants stay testable and harder to bypass accidentally.
- **Ruff + pre-commit:** Fast, consistent formatting and lint on every commit; low-friction “local CI” without fighting the stack.
- **Static typing discipline:** Pydantic at API boundaries plus typed repositories/services; I used editor type checking (e.g. Pylance/Pyright-style feedback) while coding so refactors stayed safe as the model grew.
- **Hosted CI:** There is no `.github/workflows` in this repo yet; the repeatable gate today is `uv run pytest` plus pre-commit. Adding a one-job GitHub Action to run those on push would be a small follow-up if reviewers expect remote CI.

---

## Initial task: seed script

The seed script was out of date: it imported non-existent top-level modules, read the wrong JSON file, used old model field names (`species_name`, `pokemon_name`, `confirmed`), bypassed Alembic with `create_all`, and could not import `app` when run as `python scripts/seed.py` until the project was packaged in `pyproject.toml`. It now runs migrations first, loads `data/pokedex_entries.json`, inserts with the current schema, and supports optional `SEED_SIGHTING_COUNT` for faster local and test runs.

Broader repo hygiene: `.env` / `.env.example`, Alembic-only schema, and pytest loading `.env` + `.env.test` with ephemeral `data/pytest_*.db` files per test so dev and test data stay isolated.

## Refactor: identity, roles, and auth (`chore/refactor-endpoints`)

- **One user row, role-specific profiles:** `app_users` holds shared identity (email, display name, status, id); `trainers` / `rangers` are thin FK extensions so we are not duplicating user fields per role while sightings still reference rangers cleanly.
- **Roles in the DB:** `role` and `status` use check constraints so the database enforces trainer/ranger and active/disabled rules alongside the API.
- **Indexes:** `idx_app_users_email_norm` speeds “email already registered” checks; `idx_app_users_role_name` on `(role, display_name_normalized)` supports lookup by normalized name within a role; unique `display_name_normalized` gives a single canonical handle per display identity.
- **Sightings and mutations:** The starter described `X-User-ID`; the implementation uses **signed bearer JWTs** so the server verifies the caller instead of trusting a raw UUID header. Role checks (ranger vs trainer) still enforce the same boundaries described in the brief.

## Feature 1: Sighting filters and list pagination

**Goal:** Let coordinators query sightings with combined filters and paginate without loading entire regions into memory.

**API:** `GET /sightings` accepts typed query params for `pokemon_id`, `region`, `weather`, `time_of_day`, `ranger_id`, `date_from` / `date_to`, plus `limit` and optional **cursor** (opaque token for stable “latest first” paging). Responses include `items`, `total_count`, and `next_cursor`. The prompt suggested `limit`/`offset`; I used **cursor + limit** for stable ordering under concurrent inserts (offset pagination can skip or duplicate rows when data changes). If evaluators expect literal `offset`, that would be a small additive change.

**Implementation:** `SightingRepository` centralizes filter construction with an allowlisted map and parameterized SQLAlchemy predicates. Composite indexes on `sightings` align with common filter and sort patterns.

**Data quality:** SQLite `CHECK` rules mirror domain enums and non-empty/trimmed text; registration uses Pydantic `EmailStr` plus `email-validator` so bad emails fail at the API while constraints still protect bypass paths.

## Feature 2: Research campaigns

**Goal:** Model planned research efforts with a strict lifecycle and tight coupling to sightings.

**API (aligned with the suggested shape):** `POST /campaigns` (starts in `draft`), `GET` / `PATCH` `/campaigns/{id}`, `POST /campaigns/{id}/transition`, `GET /campaigns/{id}/summary`.

**Rules enforced:** Only **active** campaigns accept new sightings; invalid lifecycle transitions are rejected forward-only; completing a campaign **locks** linked sightings so they cannot be edited or deleted. Summary aggregates total sightings, unique species, contributing rangers, and observation date range.

Domain and service layers hold transition and locking rules so routers stay thin and tests can target behavior directly.

## Feature 3: Peer confirmation

**Goal:** Let rangers corroborate each other’s sightings without gaming the system.

**API:** `POST /sightings/{id}/confirm` and `GET /sightings/{id}/confirmation`. The confirming user must be a **ranger**, must not be the original reporter, and each sighting can be confirmed at most once. Confirmed rows record who confirmed and when. Campaign-locked sightings cannot be mutated through this flow.

**Persistence:** Database constraints and foreign keys back the rules (e.g. confirmer ≠ reporter) so invariants are not only application-level. The seed script generates confirmations with a distinct confirmer so seeded data respects the schema.

Regional summary (Feature 4) surfaces **confirmed vs unconfirmed** counts so confirmation status feeds downstream reporting.

## Feature 4: Regional research summary and performance

**Goal:** `GET /regions/{region_name}/summary` for quarterly-style reporting: total sightings (with confirmed / unconfirmed split), unique species, top 5 species and top 5 rangers by count, and breakdowns by weather and time of day.

**Queries:** Implemented as focused aggregate SQL (counts, grouped breakdowns, limited top-N subqueries) scoped by normalized region, relying on the same indexing strategy as the list endpoint so large regions stay practical.

**Pokédex list slowness:** Addressed in the same effort as other read paths (indexes and avoiding accidental full-table patterns where relevant); see tests under `tests/routers/test_regions.py` for shape and basic timing sanity.
