# EventMesh — Phase 0 Report

_Foundation & Deployment. Status: **complete**. Source of truth: [`../ARCHITECTURE_V2.md`](../ARCHITECTURE_V2.md)._

## Overview

Phase 0 reset the repository and stood up a production-grade, domain-driven
FastAPI backend, connected it to Supabase Postgres, and deployed it to Render —
all wired through CI, migrations, and environment-driven configuration.

## Stack (as deployed)

| Concern | Choice |
|---|---|
| API | FastAPI (Python 3.12), async SQLAlchemy 2, Pydantic v2 |
| DB | Supabase PostgreSQL (project `eventmesh`, region ap-south-1 / Mumbai) |
| Migrations | Alembic (async) |
| Auth (Phase 1) | Supabase Auth — FastAPI validates JWTs (JWKS, HS256 fallback) |
| Packaging | uv + pinned `uv.lock` |
| Container | Docker (`backend/Dockerfile`) |
| Backend host | Render (Singapore, free plan, Docker runtime) |
| CI / Sync | GitHub Actions (CI on push/PR; provider sync every 6h) |
| Logging | structlog (JSON in prod) |

## What was built

- **Domain-driven modular monolith** under `backend/app/`: `core/` (config,
  database, logging, security, exceptions, pagination), `api/` (v1 router +
  health), `db/` (base + migrations), `modules/` (`users` implemented;
  `organizers`, `events`, `providers`, `sync`, `search`, `notifications`
  scaffolded). Provider and Search hexagonal interfaces defined.
- **Fail-fast configuration** — bans SQLite always; requires Supabase URL,
  admin token, and a non-local database in production. The app refuses to boot
  otherwise.
- **Health endpoints** — `/health` (overall), `/health/live` (liveness),
  `/health/ready` (readiness with a DB probe → 503 if the DB is unreachable).
- **Baseline migration** `716024f441aa` — `profiles` table + `user_role` enum,
  with a hardened `downgrade` that also drops the enum type.

## Infrastructure

| Resource | Value |
|---|---|
| Supabase project ref | `xzxuahmqljsvzcsvthjz` |
| Supabase region | ap-south-1 (Mumbai) |
| DB connection | Session pooler, `postgresql+asyncpg`, `statement_cache_size=0` |
| Pooler host note | `aws-1-ap-south-1.pooler.supabase.com` (not `aws-0-…`) |
| Render service | `eventmesh-api` (`srv-d93r4jlaeets73ed3sq0`) |
| **Live URL** | **https://eventmesh-api.onrender.com** |
| Render region / plan | Singapore / free / Docker, auto-deploy on `main` |
| CI | GitHub Actions — ruff (lint+format) + pytest |
| Sync workflow | GitHub Actions cron `0 */6 * * *` → `POST /api/v1/admin/sync` (skips until Phase 4) |

Secrets live only in the gitignored `backend/.env` locally and as Render
service env vars / GitHub Actions secrets in the cloud. Nothing sensitive is
committed (`.env.example` holds placeholders only).

## Verification results

| Check | Result |
|---|---|
| Lint / format (`ruff`) | clean |
| Tests (`pytest`) | 10/10 pass |
| CI on `main` | green |
| Local uvicorn boot | `/health`, `/health/live`, `/health/ready` all 200 |
| Alembic downgrade → upgrade cycle | clean (profiles+enum drop/recreate verified) |
| Live DB connection | verified (`SELECT 1`, `current_user=postgres`) |
| Production boot on Render | `/health` → `{"status":"healthy","environment":"production"}` |
| Docker secrets embedded? | no — secrets untracked + `.dockerignore` excludes `.env*`/`*.db` |

## Local development

```bash
cd backend
cp .env.example .env        # fill in values
uv sync --dev
uv run uvicorn app.main:app --reload    # http://localhost:8000 (/docs, /health)
uv run pytest -q
uv run alembic upgrade head             # against DATABASE_URL
# Docker (bundled Postgres for local only):
docker compose up --build
```

## Known limitations / risks

- **Render free tier sleeps** after ~15 min idle → first request cold-starts
  (~50s). Accepted for MVP.
- **Git history** still contains the (rotated, obsolete) original Eventbrite key
  and the old `venv`. History rewrite is deferred to pre-launch by decision.
- `EVENTMESH_API_URL` GitHub secret is intentionally unset until Phase 4 (the
  `/admin/sync` endpoint does not exist yet), so the sync workflow no-ops.

## Next: Phase 1 — Authentication

Supabase JWKS verification, Google Login + Email OTP, protected routes, and
frontend auth integration. The `profiles` table and JWT verification scaffolding
are already in place.
