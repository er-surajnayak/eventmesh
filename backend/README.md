# EventMesh Backend

Production-grade backend for **EventMesh** — an Event Aggregation **+** Hosting
platform (NayakLabs). Built as a domain-driven modular monolith. See
[`../ARCHITECTURE_V2.md`](../ARCHITECTURE_V2.md) for the full design (source of truth).

## Tech Stack
- **Framework**: FastAPI (Python 3.12)
- **ORM / Migrations**: SQLAlchemy 2 (async) + Alembic
- **Validation**: Pydantic v2
- **Database**: Supabase PostgreSQL (asyncpg)
- **Auth**: Supabase Auth — FastAPI validates JWTs only (JWKS, HS256 fallback)
- **Scheduler**: GitHub Actions → `POST /api/v1/admin/sync` every 6h (no in-process scheduler)
- **Packaging / Container**: uv + Docker; hosted on Render

## Project Layout (domain-driven)
```
app/
├── core/            # config, database, logging, security (JWT), exceptions, pagination
├── api/v1/          # router aggregation + shared deps
├── db/              # declarative base + Alembic migrations
├── shared/          # cross-cutting schemas
└── modules/         # one folder per domain (router/service/repository/schemas/models)
    ├── users/           # profiles + roles                (Phase 1–2)
    ├── organizers/      # organizations, membership       (Phase 2)
    ├── events/          # native / imported / visible      (Phase 3)
    ├── providers/       # pluggable sources (one interface) (Phase 4)
    ├── sync/            # sync orchestration               (Phase 4)
    ├── search/          # abstract SearchService           (Phase 5)
    └── notifications/   # scaffold only (no delivery in MVP)
```

## Local Development
```bash
cd backend
cp .env.example .env                 # fill in values
uv sync --dev                        # create .venv + install (lockfile-pinned)
uv run uvicorn app.main:app --reload # http://localhost:8000  (/health, /docs)
uv run pytest -q                     # tests
uv run ruff check . && uv run ruff format .
```

### With Docker (bundled Postgres for local only)
```bash
docker compose up --build            # api on :8000, postgres on :5432
```

### Migrations (Alembic)
```bash
uv run alembic revision --autogenerate -m "message"
uv run alembic upgrade head
```

## Endpoints (current)
- `GET /health` — liveness/readiness (used by Render health check)
- `GET /api/v1/users/me` — caller profile (requires Supabase JWT)

More endpoints land per phase; see `ARCHITECTURE_V2.md` §9.
