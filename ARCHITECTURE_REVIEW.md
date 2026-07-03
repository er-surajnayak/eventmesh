# EventMesh — Architecture Review

_Prepared: 2026-07-03. Scope: full-repository read, no code changes. This document describes the current state, evaluates the frontend↔backend integration, catalogs issues, and proposes a phased plan. **Awaiting approval before any code changes.**_

---

## 1. Executive Summary

EventMesh is a full-stack event-aggregation app: a **React 18 + Vite** single-page frontend and a **FastAPI (async SQLAlchemy)** backend that scrapes/pulls events from Eventbrite, Meetup, Luma, Partiful (stub), and Ticketmaster, normalizes them into one schema, and serves them over a REST API.

The core architecture is sound and cleanly layered. The frontend already talks to the backend (`GET /events/`). However, the integration is **brittle** (hard-coded URLs, mismatched origins, no API abstraction, no pagination, silent failures) and the deployment story has a **fundamental mismatch**: an APScheduler + SQLite design deployed to Vercel serverless, where neither background jobs nor a writable SQLite file survive. There are also **committed secrets and a committed `venv/`** that need urgent attention.

The work below is organized so the highest-risk, lowest-effort fixes (secrets, repo hygiene, integration wiring) land first, and the deeper deployment/data-source rework follows.

---

## 2. Current State

### 2.1 Repository Layout

```
eventmesh/
├── README.md
├── .gitignore                 # ignores node_modules, dist — but NOT venv
├── frontend/                  # React + Vite SPA
│   ├── index.html
│   ├── vite.config.js         # bare @vitejs/plugin-react, no proxy/env
│   ├── package.json           # react, react-dom only (no router, no fetch lib)
│   └── src/
│       ├── main.jsx
│       ├── App.jsx            # state container + data fetching
│       ├── index.css          # design tokens (CSS vars), global styles
│       ├── components/        # 13 components, all inline-styled
│       ├── data/events.js     # static fallback + filter constants
│       ├── hooks/useRevealOnScroll.js
│       └── utils/             # filters.js (now unused), formatDate.js
└── backend/                   # FastAPI service
    ├── app/
    │   ├── main.py            # app, CORS, lifespan scheduler, /sync /health
    │   ├── core/              # config.py (pydantic-settings), database.py
    │   ├── models/event.py    # SQLAlchemy Event model
    │   ├── schemas/event.py   # Pydantic EventCreate / EventResponse
    │   ├── api/routes/events.py
    │   ├── scheduler/jobs.py  # fetch + cleanup jobs
    │   ├── services/          # 7 source integrations (scrapers + APIs)
    │   └── utils/dedup.py     # upsert-by-URL
    ├── init_db.py  seed.py
    ├── requirements.txt (unpinned)  runtime.txt (3.12)
    ├── Dockerfile  docker-compose.yml  Procfile  vercel.json
    ├── deploy_gcp.sh  deploy_oracle.sh
    ├── .env  .env.example                # ⚠ .env committed with a key
    ├── eventmesh.db                       # ⚠ SQLite DB committed
    └── venv/                              # ⚠ 2,090 files committed
```

### 2.2 Frontend Architecture

- **Single page, no router.** Navigation is anchor-scroll (`#discover`, `#how`, `#sources`) via `App.explore()` and `<a href="#…">`. `react-router` is not a dependency.
- **`App.jsx` is the one stateful container.** It holds `filters`, `events`, `loading`, `tweaks`, `tweakMode`, applies the accent color to CSS variables, and **fetches events directly** in a `useEffect` keyed on `filters`.
- **Component tree** (all presentational, all inline-styled — no CSS modules, no Tailwind, no styled-components):
  `Navbar → Hero(MeshBackground) → FilterBar → EventGridSection(EventCard/SkeletonCard/StaticMesh) → HowItWorks → SourcesStrip → Footer → TweaksPanel`.
- **Design system** lives in `index.css` as CSS custom properties (`--bg`, `--fg`, `--accent`, `--radius`, …) plus a small set of keyframes and `.reveal` scroll-in animation. `UIPrimitives.jsx` centralizes icons, `LogoMark`, `PlatformBadge`, `PriceTag`.
- **`data/events.js`** still exports `EVENTS` (12 hard-coded events, now unused for rendering) and the filter constants `CITIES`, `DATE_FILTERS`, `PRICE_FILTERS`, `TYPE_FILTERS` (still used by `FilterBar`).
- **`utils/filters.js`** implements client-side filtering that is now **dead code** — filtering moved server-side — and it uses a different filter vocabulary (`date: 'any'`, `city: 'All cities'`) than the live app.
- **`TweaksPanel` + postMessage** (`__activate_edit_mode`) is a live-design/embed tooling artifact, not a product feature.

### 2.3 Backend Architecture

- **FastAPI** with an `asynccontextmanager` **lifespan** that (a) `create_all()`s tables and (b) starts an **APScheduler `AsyncIOScheduler`** with two interval jobs: `fetch_and_store_events` (every 30 min) and `cleanup_old_events` (daily).
- **Async SQLAlchemy 2.0**; `core/database.py` adapts the URL for SQLite (`aiosqlite`, `check_same_thread`) vs Postgres (`asyncpg`, `ssl=require`).
- **`Event` model**: UUID PK, `url` unique (dedup key), indexed `start_time`/`city`/`status`, plus `platform`, `is_free`, `is_online`, `image_url`, timestamps.
- **Schemas**: `EventCreate` (ingestion) and `EventResponse` (frontend shape with derived `category`/`hue`). `EventListResponse = { total, events }`.
- **`GET /events/`** supports `city`, `free`, `online`, `date_range` (today/week/month), `search`, `limit`, `offset`; computes `total` via a count subquery; derives `category` from title/description keywords and maps to a `hue`.
- **Ingestion services** (`app/services/`):
  | Source | Mechanism | State |
  |---|---|---|
  | Eventbrite | HTML scrape (LD+JSON) | active in job |
  | Eventbrite | Official API (Bearer) | present, not wired into job |
  | Meetup | HTML scrape (LD+JSON / `__NEXT_DATA__`) | active in job |
  | Meetup | GraphQL API | present, not wired into job |
  | Luma | HTML scrape (`__NEXT_DATA__`/apollo) | active in job |
  | Ticketmaster | Official API | active in job |
  | Partiful | Stub (returns `[]`) | placeholder |
- **`utils/dedup.save_events`** upserts by `url` (update if exists, else insert), commit-with-rollback.

### 2.4 Current Integration & Deployment

- **Frontend → backend call** (`App.jsx`): builds query params from filters and fetches
  `` `${baseUrl}/events/?…` `` where `baseUrl` is chosen by
  `window.location.hostname !== 'localhost' ? 'https://eventmesh-b.vercel.app' : 'http://localhost:8000'`.
- **CORS** (`main.py`) allows `http://localhost:5173` and `https://eventmesh-chi.vercel.app`.
- **Backend on Vercel** (`backend/vercel.json`): `@vercel/python` serving `app/main.py`, with a **cron** hitting `/sync` daily.
- **Alt deploys**: `Dockerfile` + `docker-compose.yml` (Postgres 15 + backend), `Procfile` (uvicorn), and `deploy_gcp.sh` / `deploy_oracle.sh` (systemd + SQLite + 2 GB swap on free-tier VMs).

---

## 3. Identified Issues

Ordered by severity. IDs are referenced by the phased plan in §5.

### 3.1 Critical — Security & Repo Hygiene

- **[S1] Committed secret.** `backend/.env` is tracked and contains `EVENTBRITE_API_KEY=OA2RI6C76SJTWWS6DI4H`. Must be rotated and the file removed from tracking (`.gitignore` it). Only `.env.example` should be committed.
- **[S2] Hard-coded API key in source.** `TicketmasterService` defaults `api_key` to a literal placeholder key. Move to config/env.
- **[S3] `venv/` committed** — 2,090 files of a Python 3.9 virtualenv are in git, bloating the repo and pinning a stale interpreter (while `runtime.txt` says 3.12). Untrack and ignore.
- **[S4] `eventmesh.db` committed** — a binary SQLite DB in version control; churns on every run. Untrack and ignore.
- **[S5] Weak `/sync` auth.** `api_key == settings.EVENTBRITE_API_KEY[:8]` conflates a data-source key with an admin token, and **crashes** (`TypeError` on `None[:8]`) if the key is unset. It also returns `({...}, 401)`, which FastAPI serializes as a 200 body, not a 401. Needs a dedicated admin token and proper status handling.

### 3.2 High — Deployment Model Mismatch

- **[D1] APScheduler on serverless.** Vercel functions are ephemeral and event-driven; the lifespan scheduler will not run reliably (no long-lived process). Background sync effectively depends on the `/sync` cron instead — but see D2.
- **[D2] SQLite on serverless.** With `DATABASE_URL=sqlite`, the DB lives on an ephemeral/read-only function filesystem. Writes from `/sync` won't persist and won't be visible to read requests. The Vercel path effectively needs a managed Postgres.
- **[D3] Origin/base-URL triad is inconsistent.** Frontend fetches `eventmesh-b.vercel.app`; CORS allows `eventmesh-chi.vercel.app`; there is no committed frontend deployment config. These three must be reconciled and centralized.
- **[D4] Broken deploy scripts.** `deploy_gcp.sh` / `deploy_oracle.sh` call `python create_db.py`, which does not exist (the file is `init_db.py`). Oracle script also hard-codes `EVENTBRITE_API_KEY=YOUR_KEY_HERE`.

### 3.3 Medium — Frontend↔Backend Integration Correctness

- **[I1] No pagination wired.** Frontend never sends `limit`/`offset`, so only the first **20** events ever render, regardless of how many match. Backend already returns `total`, which the UI ignores.
- **[I2] `resultCount` is misleading.** `FilterBar` shows `events.length` (current page ≤ 20), not the backend `total`.
- **[I3] Filter-reset vocabulary mismatch.** `EmptyState` resets to `{ city: 'All cities', date: 'any', price: 'all' }`, but the app's initial/valid values are `city: 'San Francisco'`, `date: 'all'`. Reset produces a state the `FilterBar` controls can't represent and that the backend maps oddly.
- **[I4] No API abstraction / hard-coded URLs.** The fetch, base-URL selection, and param mapping live inline in `App.jsx`. There is no `VITE_API_BASE_URL`, no `api/` client module, no Vite dev proxy.
- **[I5] Silent failure UX.** On fetch error the app only `console.error`s and leaves `events` unchanged; there is no error state, retry, or empty-vs-error distinction.
- **[I6] Static "live" numbers.** `Hero` ("3 sources · 2,184 events") and `SourcesStrip` (per-platform counts) are hard-coded, not derived from `total`/sources — misleading once real data flows.

### 3.4 Medium — Backend Correctness & Quality

- **[B1] Fragile scrapers as the primary source.** HTML/`__NEXT_DATA__` scraping of Eventbrite/Meetup/Luma is brittle and ToS-sensitive; the official-API services exist but aren't used by the job. `Partiful` is a stub. Scraping also needs a headless browser for JS-hydrated sites.
- **[B2] No migrations.** `alembic` is a dependency but tables are created via `create_all()`; schema changes have no migration path.
- **[B3] Unpinned dependencies.** `requirements.txt` has no versions → non-reproducible builds.
- **[B4] Postgres-only UUID type on SQLite.** `sqlalchemy.dialects.postgresql.UUID` is used on a model that also runs on SQLite; works by accident but is dialect-coupled.
- **[B5] Search uses `LIKE`/`contains`.** Fine at small scale; won't scale and is case/locale-limited. No full-text index.
- **[B6] Dead/duplicate code.** `Event.to_dict` is unused (route builds `EventResponse` inline); two Eventbrite and two Meetup service implementations coexist.
- **[B7] No tests, no structured logging, no rate-limiting/observability** around outbound scraping.

### 3.5 Low — Frontend Quality

- **[F1] Dead client-side filtering** (`utils/filters.js`) and unused `EVENTS` export.
- **[F2] Fake geolocation** in `FilterBar` (always returns "San Francisco").
- **[F3] Inline styles everywhere** — no shared style layer beyond CSS vars; heavy duplication, harder theming/maintenance.
- **[F4] No `.env` usage, no error boundary, no `loading`/`error`/`empty` state machine, no `react` key strategy issues but no `total`-driven "load more".**
- **[F5] Design/embed tooling (`TweaksPanel`, postMessage) ships in the product bundle.**

---

## 4. Proposed Backend Integration Strategy

The goal is a **clean, environment-driven contract** between the SPA and the API, plus a deployment topology that actually supports background ingestion.

### 4.1 API Contract (formalize what exists)

- Keep `GET /events/` as the read endpoint returning `{ total, events }`. Frontend consumes `total` for pagination and result counts.
- Add lightweight support endpoints as needed: `GET /health` (exists), and optionally `GET /meta` (source list + live counts) to replace hard-coded Hero/SourcesStrip numbers ([I6]).
- Document query params and the `EventResponse` shape in the backend README as the single source of truth.

### 4.2 Frontend Data Layer

- Introduce `src/api/client.js`: a single `fetchEvents(filters, { limit, offset })` that maps UI filter state → query params, reads the base URL from **`import.meta.env.VITE_API_BASE_URL`**, and returns `{ total, events }`.
- Replace the inline `App.jsx` fetch with this client; add explicit `loading` / `error` / `empty` states and a retry path ([I5]).
- Wire pagination/"load more" using `total` and `offset` ([I1], [I2]).
- Add a **Vite dev proxy** (or env file) so local dev points at `http://localhost:8000` without host-string sniffing ([I4], [D3]).

### 4.3 Configuration & CORS

- Centralize allowed origins in backend config (env-driven list), and make the frontend base URL env-driven. Reconcile the `eventmesh-b` vs `eventmesh-chi` naming so origin, CORS, and base URL agree ([D3]).

### 4.4 Deployment Topology (recommended)

- **Managed Postgres** (e.g., Neon/Supabase/RDS) as the shared datastore for any hosted deployment — required for the Vercel path to work at all ([D2]).
- **Ingestion runs on a long-lived host or a real scheduler**, not in a serverless function:
  - Option A (recommended for free-tier): the **GCP/Oracle VM + systemd** path already scripted — run the FastAPI app *with* the APScheduler lifespan there, backed by managed (or local) Postgres. Fix the scripts ([D4]).
  - Option B (serverless read API): keep the read API on Vercel against managed Postgres, and move ingestion to **Vercel Cron → `/sync`** (make `/sync` idempotent, authenticated, and time-bounded) **or** an external scheduler/worker. Drop APScheduler in this mode ([D1]).
- Decide **one** primary topology; document the other as "alternative."

### 4.5 Data Sources

- Prefer **official APIs** (Eventbrite, Meetup GraphQL, Ticketmaster) over scraping where credentials allow; keep scrapers as clearly-labeled fallbacks. Consolidate the duplicate services ([B1], [B6]).

---

## 5. Phased Implementation Plan

Each phase is independently shippable. Nothing here is executed until you approve.

### Phase 0 — Security & Hygiene (fast, do first)
- [S1] Rotate the Eventbrite key; `git rm --cached backend/.env`, add to `.gitignore`, keep `.env.example`.
- [S3] Untrack `backend/venv/`; add `venv/` to `.gitignore`.
- [S4] Untrack `backend/eventmesh.db`; add `*.db` to `.gitignore`.
- [S2] Move the Ticketmaster key to config/env.
- Also ignore `.DS_Store` globally.
- _Note: [S1]/[S3]/[S4] remove files from the working tree's tracking but not from history — call out whether history rewrite is desired._

### Phase 1 — Integration Correctness (frontend↔backend)
- [I4] Add `VITE_API_BASE_URL`, `src/api/client.js`, and a Vite dev proxy; remove host-string sniffing.
- [I3] Fix the filter-reset vocabulary to match `FilterBar`/initial state.
- [I5] Add `error` state + retry; distinguish empty vs error.
- [I1][I2] Wire pagination and drive `resultCount` from backend `total`.

### Phase 2 — Backend Robustness & Auth
- [S5] Add a dedicated admin token; fix `/sync` auth and proper 401 handling; make sync idempotent/time-bounded.
- [B3] Pin `requirements.txt`.
- [B2] Introduce Alembic migrations (baseline from current schema).
- [B6] Remove dead code (`to_dict`, unused duplicate services) once the active path is chosen.
- [B7] Add structured logging + minimal tests for the `/events` route and `dedup`.

### Phase 3 — Deployment Reconciliation
- [D3] Reconcile origins/base URL; env-drive CORS.
- [D2][D1] Stand up managed Postgres; pick the ingestion topology (VM+systemd _or_ serverless+cron) and align config accordingly.
- [D4] Fix `deploy_gcp.sh`/`deploy_oracle.sh` (`init_db.py`, env handling).
- Add a committed frontend deploy config (Vercel/Netlify) with the API base URL as a build-time env var.

### Phase 4 — Data Sources & Product Polish
- [B1] Prefer official APIs; label scrapers as fallback; implement or remove the Partiful stub.
- [I6] Add `/meta` (or reuse `total`) and drive Hero/SourcesStrip from real data.
- [F1][F2][F5] Remove dead client filtering, fake geolocation, and design-only tooling from the product bundle (or gate it).
- [B5] Consider full-text search if catalog grows.

### Phase 5 — Optional Refactors (only if desired)
- [F3] Extract a shared style layer (CSS modules / small utility system) to reduce inline-style duplication.
- [B4] Use a dialect-neutral UUID/type strategy.

---

## 6. Open Questions (need your input before Phase 0+)

1. **Primary deployment target** — Vercel (serverless + managed Postgres) or the free-tier VM (systemd + APScheduler)? This drives Phases 2–3.
2. **Git history** — for the committed secret / DB / `venv`, do you want a full history rewrite (`git filter-repo`), or just stop tracking going forward?
3. **Data sources** — do you have official API credentials (Eventbrite, Meetup, Ticketmaster) so we can prefer APIs over scraping? Is scraping acceptable given each platform's ToS?
4. **Scope of this engagement** — integration wiring + hygiene only, or the full backend/deployment rework through Phase 4?
5. **Product intent for `TweaksPanel`** — keep as an internal/embed tool, or remove from the shipped app?

---

_No code has been modified. Please review, answer the open questions in §6, and tell me which phases to proceed with._
