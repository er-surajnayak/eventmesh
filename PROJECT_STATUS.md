# EventMesh — Project Status

_Last updated: 2026-07-04 · Source of truth for a fresh session, alongside
[`ARCHITECTURE_DECISIONS.md`](ARCHITECTURE_DECISIONS.md), [`ROADMAP.md`](ROADMAP.md),
[`DEPLOYMENT.md`](DEPLOYMENT.md), and [`ARCHITECTURE_V2.md`](ARCHITECTURE_V2.md)._

EventMesh (NayakLabs) is an **Event Aggregation + Hosting** SaaS: discover events
aggregated from external providers, and host/register for native events.

## Live state

| Piece | Value |
|---|---|
| Repo | `github.com/er-surajnayak/eventmesh` (main branch; `gh` account `imsuru` = same owner) |
| Backend | FastAPI (Python 3.12) on **Render** — https://eventmesh-api.onrender.com (`srv-d93r4jlaeets73ed3sq0`), Docker, free tier (cold starts) |
| Database | **Supabase Postgres**, project `eventmesh` ref `xzxuahmqljsvzcsvthjz`, region ap-south-1 (Mumbai) |
| Auth | Supabase Auth (Google + Email OTP, no passwords); FastAPI validates JWTs (JWKS ES256) |
| Frontend | React + Vite + react-router on **Vercel** (`eventmesh.xyz`) — design language dark/CSS-var |
| Sync | **GitHub Actions** every 6h → `POST /api/v1/admin/sync` |
| Alembic head | `313406be2548` |
| Tests | 69 (pytest), CI green on every push this session |

## What's built (Phases 0–4 complete)

- **Phase 0 — Foundations**: domain-driven modular monolith, env-driven config
  with fail-fast validation, structured logging, async SQLAlchemy 2, Alembic
  (migrate-on-container-start), Dockerfile (uv), CI, health endpoints
  (`/health`, `/health/live`, `/health/ready`).
- **Phase 1 — Auth**: Supabase JWKS verification, `AuthProvider` + `ProfileProvider`
  (auth separated from profile), protected routes, `/users/me`, session persistence.
- **Phase 2 — Identity & Organizations**: `profiles` (roles), `organizations` +
  `organization_members` (multi-member, `org_role`), become-organizer, slug
  uniqueness, org status/type, authorization.
- **Phase 3 — Event Management**: native events full lifecycle (draft→preview→
  pending_review→published→hidden→cancelled→archived) via dedicated business
  actions; event type/visibility, venue/coords/timezone, capacity + waitlist,
  policies; registration; public browsing with visibility; **organizer dashboard,
  multi-step wizard with draft autosave, preview/publish** (frontend).
- **Phase 4 — Event Aggregation Engine**:
  - 4A: provider framework (`BaseProvider`, `NormalizedEvent`), dedup infra
    (`dedup_hash`, provider priority), `imported_events` + `sync_runs`, fail-soft
    `SyncOrchestrator` with per-provider health + sync reports, admin `/admin/sync`.
  - 4B: **Eventbrite** connector (official API; pagination, retry/backoff,
    rate-limit).
  - 4C: **Meetup** connector (responsible HTML scraping, BeautifulSoup JSON-LD).
  - 4D: **Luma** connector (structured-data first: JSON-LD → `__NEXT_DATA__` →
    Open Graph). Shared `ScrapeClient`.
  - 4E: **merge engine** (deterministic canonical: priority → completeness →
    stable tiebreak), **`visible_events` PostgreSQL VIEW** (native published ∪
    imported canonical; provenance via `sources[]`), `GET /events` public feed +
    search over the visible model.

## Public/API surface (v1, under `/api/v1`)

- Public: `GET /events` (visible feed: q/city/free/online), `GET /events/{slug}`
  (native detail), `GET /organizations/{slug}`.
- Auth: `GET/PATCH /users/me`, `POST /users/me/become-organizer`,
  `/me`… saved/follows scaffolding, `GET /registrations`.
- Organizer: `POST /organizations`, `…/events` CRUD, `…/events/{id}/{action}`
  lifecycle, attendee list.
- Registration: `POST/DELETE /events/{slug}/register`.
- Admin (X-Admin-Token): `POST /admin/sync`, `GET /admin/sync/runs`.

## Known pending / follow-ups

1. **Eventbrite token invalid** — prod sync returns 401; needs a valid Eventbrite
   **private OAuth token** in `backend/.env` + Render env `EVENTBRITE_API_KEY`.
   Connector is correct (mocked tests pass); Meetup + Luma work live.
2. **Frontend not yet wired to `GET /events`** — the landing page still shows old
   static/legacy data; the new aggregation feed is served but unconsumed. (A
   natural Phase 5 "Discovery Platform" task.)
3. **CORS browser confirmation** — Render CORS allows `eventmesh.xyz`,
   `www.eventmesh.xyz`, `localhost:5173` (verified server-side); confirm
   login + no CORS errors in-browser once Vercel env vars are set.
4. **Waitlist auto-promotion** not implemented (cancel doesn't promote a
   waitlisted registrant) — intentional MVP limitation.
5. **Imported-event expiry/retention** not implemented (view filters past events
   by `start_time`; stale-but-future events linger). Retention: archive after
   completion, delete after 90 days — future job.
6. **Git history** still contains the original (rotated/obsolete) Eventbrite key +
   old `venv` — history rewrite deliberately deferred to pre-launch.
7. **Sync workflow** checks HTTP 200 (endpoint health), not report `status` — a
   failing provider shows in the report body but keeps the workflow green.

## Non-obvious operational facts

- Supabase session pooler host is **`aws-1-ap-south-1.pooler.supabase.com:5432`**
  (NOT `aws-0-…`, which returns "tenant not found"); scheme `postgresql+asyncpg`,
  `statement_cache_size=0`; the DB password is `%40`-encoded (contains `@`).
- Set GitHub secrets via **stdin** (`printf '%s' val | gh secret set NAME`) — NOT
  `--body -` (that stores the literal `-`).
- Run **`ruff check`** and **`ruff format --check`** separately before commit
  (a combined `check && format` short-circuits and skips formatting → CI fails).
- Migrations run at container start (`Dockerfile` CMD: `alembic upgrade head && …`)
  because Render's free tier has no pre-deploy hook.
