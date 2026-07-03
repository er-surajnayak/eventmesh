# EventMesh — Deployment & Operations

Operational runbook. Identifiers below are non-secret; actual keys/passwords live
only in `backend/.env` (gitignored), Render env vars, Vercel env vars, and GitHub
Secrets — never in the repo.

## Topology

```
Browser ── Vercel (React/Vite, eventmesh.xyz)
   │  Supabase JWT (Google / Email OTP)
   ▼
Render (FastAPI, Docker) ── Supabase Postgres (asyncpg, session pooler)
   ▲
GitHub Actions (every 6h) ── POST /api/v1/admin/sync ── providers (Eventbrite/Meetup/Luma)
```

## Backend — Render

- Service: `eventmesh-api` (`srv-d93r4jlaeets73ed3sq0`), Docker runtime, region
  Singapore, free plan, auto-deploy on `main`. URL: https://eventmesh-api.onrender.com
- Health check path: `/health`. Blueprint: `render.yaml` (IaC).
- **Migrations run at container start** (`backend/Dockerfile` CMD:
  `alembic upgrade head && uvicorn app.main:app …`).
- `render` CLI is NOT installed; manage via the **Render API** with the account
  API key (stored in `backend/.env` as `RENDER_API_KEY`). Common ops (httpx/curl):
  - Update an env var: `PUT /v1/services/{sid}/env-vars/{KEY}` `{"value": "..."}`
  - Redeploy: `POST /v1/services/{sid}/deploys`
  - Poll deploy: `GET /v1/services/{sid}/deploys?limit=1` (status → `live`)
- **Required env vars**: `ENVIRONMENT=production`, `DEBUG=false`, `LOG_LEVEL`,
  `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `ADMIN_SYNC_TOKEN`,
  `CORS_ORIGINS`, `EVENTBRITE_API_KEY`. Config validation fails fast if the
  production-required ones are missing/localhost.

## Database — Supabase

- Project `eventmesh`, ref `xzxuahmqljsvzcsvthjz`, region ap-south-1 (Mumbai).
- **Connection string** (session pooler, IPv4, prepared-statement safe):
  `postgresql+asyncpg://postgres.xzxuahmqljsvzcsvthjz:<PW>@aws-1-ap-south-1.pooler.supabase.com:5432/postgres`
  - ⚠️ Host is **`aws-1-…`** (not `aws-0-…`). If the DB password contains `@`,
    percent-encode it (`%40`). `statement_cache_size=0` is set in the engine.
- Migrations: `uv run alembic upgrade head` (or automatic on deploy). Current head
  `313406be2548`. Schema: `profiles`, `organizations`, `organization_members`,
  `native_events`, `event_registrations`, `imported_events`, `sync_runs`, and the
  `visible_events` VIEW.
- CLI: `supabase` is installed and logged in; `supabase projects api-keys
  --project-ref <ref> -o json` yields anon + service_role keys.

## Auth — Supabase

- Providers: **Email OTP** (works out of the box) + **Google** (needs an OAuth
  client ID/secret configured in Supabase → Auth → Providers).
- JWTs are asymmetric (JWKS/ES256):
  `https://<ref>.supabase.co/auth/v1/.well-known/jwks.json`.

## Frontend — Vercel

- React + Vite + react-router; domain `eventmesh.xyz` (+ `www`).
- **Required build-time env vars** (Vite inlines at build; see
  `frontend/.env.example`): `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`
  (missing → graceful config-error screen, not a crash), `VITE_API_BASE_URL`
  (`https://eventmesh-api.onrender.com`).
- SPA deep links: `frontend/vercel.json` rewrites all paths to `/index.html`.
- After setting env vars, redeploy on Vercel.

## CI / Sync — GitHub Actions

- `.github/workflows/ci.yml`: on push/PR — `uv sync`, `ruff check`, `ruff format
  --check`, `pytest`.
- `.github/workflows/sync.yml`: cron `0 */6 * * *` (+ manual) → `POST /admin/sync`
  with `X-Admin-Token`. Checks HTTP 200 (endpoint health).
- **Secrets** (`gh secret set NAME` via **stdin**, never `--body -`):
  `EVENTMESH_API_URL=https://eventmesh-api.onrender.com`, `ADMIN_SYNC_TOKEN`
  (must match the Render env var).

## CORS

Env-configurable via `CORS_ORIGINS` (comma-separated). Currently:
`http://localhost:5173, https://eventmesh.xyz, https://www.eventmesh.xyz`.
Update via the Render API env-var PUT + redeploy; verify with an OPTIONS preflight
(`Origin` → matching `Access-Control-Allow-Origin`).

## Local development

```bash
cd backend
cp .env.example .env         # fill values (DATABASE_URL to Supabase or local pg)
uv sync --dev
uv run uvicorn app.main:app --reload      # /docs, /health
uv run pytest -q
uv run ruff check .          # run BOTH separately before commit:
uv run ruff format --check .
uv run alembic upgrade head

cd ../frontend
cp .env.example .env.local   # fill VITE_* values
npm install && npm run dev   # http://localhost:5173
```

## Gotchas (learned the hard way)

- `gh secret set NAME --body -` stores the literal `"-"`. Use stdin:
  `printf '%s' "$value" | gh secret set NAME`.
- Run `ruff check` and `ruff format --check` **separately** (`check && format`
  short-circuits and skips formatting → CI red).
- Supabase pooler host is `aws-1-…`, not `aws-0-…`.
- Alembic autogenerate does not drop Postgres enum types on downgrade — add
  `sa.Enum(name="...").drop(op.get_bind(), checkfirst=True)` by hand.
- Adding an enum column to an existing table needs the type created first
  (`postgresql.ENUM(..., create_type=False).create(bind, checkfirst=True)`).
- Render free tier sleeps after ~15 min idle → first request cold-starts (~50s).
