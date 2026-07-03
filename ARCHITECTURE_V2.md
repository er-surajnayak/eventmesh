# EventMesh — Architecture V2

_NayakLabs · Flagship Product · Production-Grade Redesign_
_Prepared: 2026-07-03 · Status: **Proposal — awaiting approval, no code changed**_

> This supersedes `ARCHITECTURE_REVIEW.md` (V1), which is now historical context describing the _as-built_ system. V2 describes the _target_ system: an **Event Aggregation + Event Hosting** SaaS.
>
> I have written this as the founding CTO would: I accept the stack decisions as final where they are genuinely fine, and I **push back explicitly** where I think a choice will cost us later. Every pushback is labelled **⚑ CTO CHALLENGE** so you can accept or reject each one individually. Nothing here is implemented until you approve.

---

## 0. Reconciling V1 → V2

| Dimension | V1 (as-built) | V2 (target) |
|---|---|---|
| Product | Aggregator only (read-only feed) | Aggregation **+** hosting, registration, favourites, follows, recommendations |
| DB | SQLite / ad-hoc Postgres | Supabase Postgres (managed) |
| Auth | None | Supabase Auth (Google + Email OTP), FastAPI validates JWT |
| Scheduler | APScheduler in-process | GitHub Actions → `POST /admin/sync` every 6h |
| Backend host | Vercel Python (broken for schedulers/SQLite) | Render |
| Frontend host | Vercel (implicit) | Vercel (explicit) |
| Events model | One `events` table | Native / Imported / Visible separation |
| Providers | Ad-hoc scraper + API classes, duplicated | One common provider interface + registry |
| Search | SQL `LIKE` | SQL FTS → Meilisearch → semantic, behind an abstraction |
| Structure | Layer-by-type | Domain-driven modular monolith |

**Carried forward from V1 as prerequisites (still unresolved, still urgent):** committed secret in `backend/.env`, committed `venv/` (2,090 files) and `eventmesh.db`, and unpinned deps. These must be cleaned in Phase 0 regardless of V2 — see §12.6.

**Frontend reality check:** the current `frontend/package.json` declares **only `react` + `react-dom`**. Tailwind, a router, and a data-fetching layer are **not installed**. "Frontend already exists, only integrate" is achievable, but integration will still require adding Tailwind + a small data/query layer + auth SDK. That's wiring, not redesign — called out in the roadmap.

---

## 1. Revised Architecture

### 1.1 System Context (C4 level 1)

```
                         ┌───────────────────────────┐
                         │   Supabase (managed)       │
                         │  ┌─────────┐  ┌─────────┐  │
                         │  │  Auth   │  │Postgres │  │
                         │  │(GoTrue) │  │ + RLS   │  │
                         │  └────┬────┘  └────┬────┘  │
                         └───────┼────────────┼───────┘
        JWT (Google/OTP)         │            │ SQL (asyncpg)
   ┌──────────────┐  login       │            │
   │   Browser    │◄─────────────┘            │
   │ React+Vite   │                           │
   │  (Vercel)    │── REST /api/v1 ──►┌────────┴─────────┐
   └──────────────┘   Bearer JWT      │  FastAPI (Render)│
                                      │  modular monolith │
                                      └───┬──────────┬────┘
                                          │          │
                       provider adapters  │          │  admin sync (token)
                        (API/GraphQL/      │          ▲
                         scrape/RSS)       ▼          │
                   ┌──────────────────────────┐   ┌───┴───────────────┐
                   │ Eventbrite / Meetup /     │   │ GitHub Actions     │
                   │ Luma / Ticketmaster / ... │   │ cron every 6h      │
                   └──────────────────────────┘   └───────────────────┘
```

### 1.2 Guiding Principles

1. **Modular monolith, not microservices.** One FastAPI deploy, internally partitioned by domain. Microservices at MVP scale would multiply infra and cost for zero benefit. We keep clean module seams so extraction is _possible_ later, not mandatory now.
2. **Hexagonal only where it pays.** Full ports/adapters everywhere is over-engineering for a small team. We apply the adapter pattern hard at exactly two boundaries where implementations genuinely vary: **providers** (API/GraphQL/scrape/RSS) and **search** (SQL/Meilisearch/semantic). Everywhere else: pragmatic service + repository.
3. **The core never knows a provider's transport.** Every provider returns the same `NormalizedEvent`. Sync, dedup, storage, and API are transport-agnostic.
4. **Imported data is never trusted into the product path directly.** Raw → normalized → validated → deduped → _then_ eligible to be visible. (Your Native/Imported/Visible instinct, formalized in §3 and §7.)
5. **Fail-soft ingestion.** One provider dying never blocks the others or corrupts existing data.
6. **Free-first, but honest about the free-tier failure modes** (see §10 Risks — this is where the biggest surprises live).

---

## 2. Updated Folder Structure (Domain-Driven Modular Monolith)

**⚑ CTO CHALLENGE — depth of DDD.** Pure DDD with separate `domain/application/infrastructure` layers _per module_ produces ~6 files before you write a line of business logic. For a free MVP built by a small team, that tax is real. My recommendation is a **lightened domain layout**: modules own their slice end-to-end (`router → service → repository → models/schemas`), with a strict rule that cross-module calls go **service-to-service, never repository-to-repository**. This gives you 80% of DDD's decoupling at 20% of the ceremony. Full hexagonal is reserved for `providers/` and `search/`. If you want strict hexagonal everywhere, say so and I'll expand it — but I'd advise against it now.

```
backend/
├── pyproject.toml                 # poetry/uv; pinned deps (replaces bare requirements.txt)
├── alembic.ini
├── Dockerfile                     # Render build
├── .env.example                   # committed; .env is NOT
├── app/
│   ├── main.py                    # app factory, router mount, middleware, lifespan (NO scheduler)
│   ├── core/                      # cross-cutting, no business logic
│   │   ├── config.py              # pydantic-settings, env-driven
│   │   ├── security.py            # Supabase JWT verify (JWKS), current_user dep
│   │   ├── database.py            # async engine + session factory
│   │   ├── logging.py             # structured JSON logging
│   │   ├── pagination.py          # shared limit/offset + cursor helpers
│   │   └── exceptions.py          # app error types → HTTP handlers
│   ├── api/
│   │   └── v1/
│   │       ├── router.py          # aggregates all module routers under /api/v1
│   │       └── deps.py            # shared deps: db session, auth, roles
│   ├── modules/
│   │   ├── users/                 # profiles mirror of auth.users
│   │   │   ├── router.py schemas.py service.py repository.py models.py
│   │   ├── organizers/            # organizations + membership + follow
│   │   │   └── ...
│   │   ├── events/                # the read model + native authoring
│   │   │   ├── router.py          # public read: list/detail/search entrypoint
│   │   │   ├── native/            # hosting: draft→preview→publish
│   │   │   ├── imported/          # normalized imported store (write-restricted)
│   │   │   ├── visible/           # projection/view read logic
│   │   │   ├── registrations/     # native-event registration
│   │   │   ├── saved/             # favourites
│   │   │   ├── domain.py          # NormalizedEvent, EventStatus, value objects
│   │   │   └── ...
│   │   ├── providers/             # HEXAGONAL boundary #1
│   │   │   ├── base.py            # EventProvider Protocol + ProviderMeta
│   │   │   ├── registry.py        # enabled providers, feature flags
│   │   │   ├── normalizer.py      # raw → NormalizedEvent
│   │   │   ├── dedup.py           # cross-provider dedup keys + grouping
│   │   │   ├── eventbrite/  meetup/  luma/         # active
│   │   │   └── devfolio/  townscript/  ticketmaster/  # scaffolded stubs
│   │   ├── sync/                  # orchestrator for /admin/sync
│   │   │   ├── router.py          # POST /admin/sync (token-guarded)
│   │   │   ├── service.py         # fetch→normalize→validate→dedup→merge→store
│   │   │   └── runs.py            # sync run bookkeeping/observability
│   │   └── search/                # HEXAGONAL boundary #2
│   │       ├── base.py            # SearchBackend Protocol
│   │       ├── sql_backend.py     # MVP: Postgres FTS
│   │       ├── meili_backend.py   # later (stub)
│   │       └── service.py         # frontend-facing search API
│   ├── shared/                    # dtos, result types, common validators
│   └── db/
│       └── migrations/            # alembic versions
├── tests/
│   ├── unit/  integration/  providers/
└── .github/workflows/
    ├── ci.yml                     # lint + test on PR
    └── sync.yml                   # cron every 6h → POST /admin/sync
```

---

## 3. Database Design

### 3.1 The Native / Imported / Visible split

**⚑ CTO CHALLENGE — "Visible Events" should be a projection, not a third write-table (at MVP).** A third physical table you write to creates a **dual-write consistency problem**: publish a native event, and now you must also keep the visible table in sync, plus handle partial failures. For MVP I recommend **Visible = a Postgres `VIEW`** (or later a **materialized view**) that unions _published_ native events and _active, canonical_ imported events. Always consistent, zero sync lag, trivial to reason about. We switch to a materialized/denormalized `events` projection **only when** search or read latency demands it (and by then Meilisearch may own that anyway). This preserves your three-concept model while avoiding a class of bugs.

### 3.2 Tables

```
auth.users                         -- managed by Supabase (do not own)
```

**Identity & social**
```
profiles
  id            uuid PK  → auth.users.id
  handle        text unique
  display_name  text
  avatar_url    text
  is_organizer  bool default false
  created_at    timestamptz

organizations
  id            uuid PK
  owner_id      uuid → profiles.id
  slug          text unique
  name, bio, avatar_url, website
  created_at

organization_members
  org_id        uuid → organizations.id
  user_id       uuid → profiles.id
  role          text  -- owner | admin | editor
  PRIMARY KEY (org_id, user_id)

organizer_follows
  user_id       uuid → profiles.id
  organization_id uuid → organizations.id
  created_at
  PRIMARY KEY (user_id, organization_id)
```

**Native events (authored on EventMesh)**
```
native_events
  id            uuid PK
  organization_id uuid → organizations.id
  title, description, cover_url
  start_time, end_time  timestamptz
  timezone      text
  city, venue, is_online, is_free, price_cents, currency
  category      text
  status        text  -- draft | preview | published | cancelled | archived
  capacity      int null
  published_at  timestamptz null
  created_at, updated_at
  -- registrations allowed ONLY for native_events
```

**Imported events (aggregated) — never written into native_events**
```
imported_events_raw                -- audit / replay / debugging
  id            uuid PK
  provider      text
  external_id   text
  raw           jsonb              -- exact upstream payload
  fetched_at    timestamptz
  sync_run_id   uuid → sync_runs.id
  UNIQUE (provider, external_id, fetched_at)

imported_events                    -- normalized + validated
  id            uuid PK
  provider      text
  external_id   text
  url           text
  title, description, image_url
  start_time, end_time, timezone
  city, venue, is_online, is_free, price_cents, currency, category
  dedup_hash    text               -- normalized(title)+date-bucket+city
  canonical_group_id uuid          -- groups cross-provider duplicates
  is_canonical  bool               -- one true per group (chosen primary)
  status        text  -- active | expired | suppressed
  first_seen_at, last_seen_at
  UNIQUE (provider, external_id)
  INDEX (dedup_hash), INDEX (canonical_group_id), INDEX (start_time), INDEX (city)
```

**Visible events (read model)**
```
-- MVP: a VIEW
CREATE VIEW visible_events AS
  SELECT 'native'   AS kind, id, title, ... , start_time, city, url=NULL
    FROM native_events   WHERE status = 'published' AND start_time > now()
  UNION ALL
  SELECT 'imported' AS kind, id, title, ... , start_time, city, url
    FROM imported_events WHERE status = 'active' AND is_canonical AND start_time > now();
-- Later: MATERIALIZED VIEW or projection table + Meilisearch index
```

**Engagement**
```
event_registrations                -- native events only
  id            uuid PK
  native_event_id uuid → native_events.id
  user_id       uuid → profiles.id
  status        text  -- registered | waitlisted | cancelled
  created_at
  UNIQUE (native_event_id, user_id)

saved_events                       -- favourites across both kinds
  user_id       uuid → profiles.id
  event_kind    text  -- native | imported
  event_id      uuid
  created_at
  PRIMARY KEY (user_id, event_kind, event_id)
```

**Ops / observability**
```
sync_runs
  id            uuid PK
  started_at, finished_at
  status        text  -- running | success | partial | failed
  totals        jsonb -- per-provider fetched/normalized/deduped/stored/errors
  error         text null
```

**⚑ CTO CHALLENGE — dedup is the hardest correctness problem here, and it is cross-provider.** The same meetup can appear on Meetup + Luma + Eventbrite with different titles/URLs. Exact-URL dedup (V1's approach) will _not_ catch these. I propose: `dedup_hash = hash(normalize(title) + start_time_rounded_to_hour + city)`, with a `canonical_group_id` linking near-duplicates and one `is_canonical` winner (priority: native > official-API provider > scraped). This is heuristic and _will_ occasionally over- or under-merge; we make it observable (a review queue) rather than pretend it's perfect. Fuzzy title matching (trigram / `pg_trgm`) is a fast follow.

### 3.3 RLS & access model

**⚑ CTO CHALLENGE — decide the trust boundary now.** Two valid models:
- **(A) FastAPI as sole trusted client** using the Supabase **service role** key; all authz enforced in the app layer. Simpler, but RLS is bypassed, so a bug in app authz is unguarded.
- **(B) RLS-first**, FastAPI forwards the user JWT so Postgres enforces row rules; defense-in-depth even if app code slips.

**Recommendation: (A) as the primary path, with RLS enabled as defense-in-depth** on user-owned tables (`saved_events`, `event_registrations`, `native_events` drafts). If the frontend ever talks to Supabase directly (e.g., realtime), RLS becomes mandatory. Pick one before we write repositories — it changes the DB session wiring.

---

## 4. Authentication Flow

Supabase Auth (GoTrue) owns identity. FastAPI is a **pure resource server** — it never issues or refreshes tokens, only validates them.

```
Browser                Supabase Auth            FastAPI (Render)         Postgres
  │  Google / Email OTP     │                        │                     │
  │────────────────────────►│                        │                     │
  │   access_token (JWT)     │                        │                     │
  │◄────────────────────────│                        │                     │
  │  GET /api/v1/me  Bearer JWT ───────────────────► │                     │
  │                          │   verify JWT (JWKS)    │                     │
  │                          │◄──── validate sig/exp/aud ──                 │
  │                          │                        │ upsert profile      │
  │                          │                        │────────────────────►│
  │◄──────────────  200 { profile } ─────────────────│                     │
```

- **Login methods:** Google OAuth + Email OTP only. No passwords. (Configured in Supabase dashboard; frontend uses `@supabase/supabase-js`.)
- **JWT validation:** verify signature, `exp`, `aud=authenticated`, issuer. **⚑ CTO CHALLENGE / heads-up:** Supabase is moving from a **shared HS256 secret** to **asymmetric signing keys (JWKS)**. Build the verifier against the **JWKS endpoint** (cache keys, refresh on `kid` miss) rather than hard-coding the legacy shared secret — otherwise we'll be rewriting auth within a release cycle.
- **Profile provisioning:** on first authenticated request, `current_user` dependency upserts a `profiles` row keyed to `auth.users.id` (JIT provisioning). No webhook required for MVP; a Supabase DB trigger is the fast-follow if we want provisioning at signup time.
- **Roles:** `is_organizer` on profile + `organization_members.role` for org-scoped permissions. Admin sync uses a **separate mechanism** (service token), not user JWTs — see §6.

---

## 5. Provider Architecture (Hexagonal Boundary #1)

### 5.1 The contract

```python
# app/modules/providers/base.py
class ProviderMeta(BaseModel):
    slug: str                 # "eventbrite"
    display_name: str
    kind: Literal["api", "graphql", "scrape", "rss"]
    enabled: bool
    ratelimit_per_min: int

class EventProvider(Protocol):
    meta: ProviderMeta
    async def fetch(self, ctx: FetchContext) -> list[NormalizedEvent]: ...
```

- `FetchContext` carries cities, time window, and an `httpx.AsyncClient` with shared timeouts/retries.
- **Every** provider returns `list[NormalizedEvent]`. Whether it hit REST, GraphQL, scraped HTML, or parsed RSS is invisible to the caller.
- `registry.py` exposes only **enabled** providers (feature-flagged via config, so Devfolio/Townscript/Ticketmaster can ship dark).

### 5.2 Normalized model (single source of truth)

`NormalizedEvent` = the same field set the DB `imported_events` expects (title, description, url, times, tz, city, venue, is_online, is_free, price, image, provider, external_id). Providers map _into_ this; nothing downstream maps _out of_ provider-specific shapes.

### 5.3 Provider roster & honesty about each

| Provider | Kind | Free? | Reality |
|---|---|---|---|
| Eventbrite | Official API | Token-gated | Public search is restricted; org/token scoping needed. Keep the scraper as a labelled fallback. |
| Meetup | **Scrape** | — | **⚑ Meetup shut down its free API; scraping is fragile + ToS-sensitive.** See §10.R1. |
| Luma | **Scrape** | — | No public API. `__NEXT_DATA__` parsing; JS-hydrated, may need headless later. §10.R1. |
| Ticketmaster | Official API | Generous free tier | Cleanest source; prioritize wiring it despite being "future" — low risk, high yield. |
| Devfolio | API/scrape (TBD) | — | Scaffold only. |
| Townscript | API/scrape (TBD) | — | Scaffold only. |

**⚑ CTO CHALLENGE — sequence Ticketmaster earlier.** It's an official, free, stable API. Meetup/Luma scraping is the riskiest, least durable part of the whole system. If discovery breadth is the near-term goal, I'd bring **Ticketmaster forward** into the first sync milestone and treat Meetup/Luma as best-effort. Pure aggregation-quality-per-unit-risk argues for it.

---

## 6. Synchronization Architecture

```
GitHub Actions (cron: every 6h)
   │  POST /api/v1/admin/sync   header: X-Admin-Token
   ▼
sync.service.run()
   ├─ for each enabled provider  (isolated try/except, per-provider timeout)
   │     fetch() → [RawEvent]                → imported_events_raw
   │     normalize() → [NormalizedEvent]
   │     validate()  (drop malformed; count) │  fail-soft
   │     dedup()     (hash + canonical group)│
   ├─ merge: upsert into imported_events (by provider+external_id)
   │         recompute canonical winner per group
   ├─ expire: mark past/absent events status='expired'
   └─ record sync_runs row (status: success | partial | failed, per-provider totals)
```

- **Trigger:** `.github/workflows/sync.yml`, `schedule: cron('0 */6 * * *')`, hitting Render with a secret admin token from GitHub Secrets.
- **Isolation:** a provider raising is caught, logged, counted, and the run continues → status `partial`. This is the explicit "if one provider fails, others continue" requirement.
- **Idempotency:** upsert by `(provider, external_id)`; re-running a sync is safe. `/admin/sync` must be safe to call twice concurrently (advisory lock on the run).
- **Auth:** admin token (header), **not** a user JWT. Rotate via GitHub Secrets + Render env.
- **Time-bounded:** each provider gets a hard timeout so a hung scrape can't exceed the request budget.

**⚑ CTO CHALLENGE — GitHub Actions cron is "free but flaky," and Render free web services sleep.** Two compounding facts:
1. GitHub scheduled workflows are **best-effort** (can be delayed 5–30+ min under load) and are **auto-disabled after 60 days of no repo activity**. Fine for a 6-hour cadence _if_ we add a monthly keepalive commit or accept occasional skips.
2. **Render free web services spin down after ~15 min idle** (~50s cold start). The 6-hourly sync will _always_ hit a cold start (acceptable), but so will the **first real user after idle** (not acceptable for UX). Mitigations: (a) accept it for MVP, (b) a lightweight keep-warm ping, or (c) move the read API to a platform without idle-sleep later. I'd document (a) for launch and plan (c) as the first paid upgrade. If sync reliability becomes critical, a **Supabase `pg_cron` + `pg_net`** call to `/admin/sync` is a more reliable free trigger than GitHub Actions — worth considering as the primary and GH Actions as backup.

---

## 7. Event Lifecycle

### 7.1 Native (hosted) events — organizer flow

```
Guest ─login→ Registered User ─"Become Organizer"→ is_organizer=true
   → Create Organization
      → Create Event (status=draft)
         → Preview (status=preview, private shareable link)
            → Publish (status=published, published_at set)
               → appears in visible_events
                  → Users Register (event_registrations)
                     → Cancelled / Archived (terminal)
```

- Registration, capacity, waitlist, and attendee lists apply **only** to native events.
- `preview` = author-visible + link-shareable, **excluded** from `visible_events`.

### 7.2 Imported (aggregated) events

```
Provider fetch → raw → normalized → validated → deduped
   → imported_events (status=active, is_canonical?)
      → if canonical & active & future → in visible_events
         → user can SAVE + CLICK-THROUGH (deep-link to source)
         → NO registration on EventMesh (we never intercept upstream checkout)
   → sync no longer sees it OR start_time passed → status=expired → drops out
```

This is the concrete meaning of "imported events never written directly into production events": they live in `imported_events`, and only _surface_ through the `visible_events` projection when they pass canonical+active+future gates.

---

## 8. Deployment Architecture

```
┌─ Vercel ──────────────┐   ┌─ Render ─────────────────┐   ┌─ Supabase ───────────┐
│ React + Vite (static) │   │ FastAPI (Docker)         │   │ Postgres + Auth      │
│ env: VITE_API_BASE_URL│──►│ env: DATABASE_URL,       │──►│ (JWKS, RLS)          │
│      VITE_SUPABASE_*  │   │  SUPABASE_JWKS_URL,      │   └──────────────────────┘
└───────────────────────┘   │  ADMIN_SYNC_TOKEN        │
        ▲                    └──────────▲───────────────┘
        │ users                         │ POST /admin/sync (X-Admin-Token)
        │                    ┌──────────┴───────────────┐
        │                    │ GitHub Actions cron 6h   │  (+ optional pg_cron backup)
        └────────────────────┘  secrets: ADMIN_SYNC_TOKEN
```

- **Config is 100% env-driven.** No hard-coded base URLs or origins (V1's `eventmesh-b` vs `eventmesh-chi` mismatch is designed out). CORS origins come from config.
- **Migrations:** Alembic runs on deploy (Render build/release step), never `create_all()` in prod.
- **Secrets:** GitHub Secrets (CI + sync token), Render env (DB URL, JWKS URL, admin token), Vercel env (API base + Supabase anon key). `.env` is git-ignored; only `.env.example` is committed.
- **Environments:** at minimum `prod`; a Supabase `staging` project is cheap insurance before we let sync write real data.

---

## 9. API Contracts (v1)

All under `/api/v1`. `[JWT]` = requires user token; `[ADMIN]` = admin token; others public.

**Events (read)**
```
GET  /events                 ?city&free&online&date_range&category&q&kind&limit&offset&cursor
                             → { total, items: VisibleEvent[], next_cursor }
GET  /events/{kind}/{id}      → VisibleEvent (native detail or imported detail)
GET  /search                 ?q&filters...   → delegates to SearchBackend (SQL now, Meili later)
```

**Me / engagement** `[JWT]`
```
GET    /me                            → Profile
PATCH  /me                            → update profile
GET    /me/saved-events               → VisibleEvent[]
POST   /me/saved-events               { kind, event_id }
DELETE /me/saved-events/{kind}/{id}
POST   /me/follows       { organization_id }
DELETE /me/follows/{organization_id}
GET    /me/registrations              → Registration[]
```

**Organizer / hosting** `[JWT]`
```
POST  /organizations                  { slug, name, ... }
GET   /organizations/{slug}           (public)
POST  /organizations/{id}/events      { ...draft }         → native_event (draft)
PATCH /events/native/{id}             update draft
POST  /events/native/{id}/preview
POST  /events/native/{id}/publish
POST  /events/native/{id}/cancel
GET   /events/native/{id}/registrations   (organizer only)
```

**Registration** `[JWT]`
```
POST  /events/native/{id}/register    → Registration
DELETE /events/native/{id}/register   → cancel
```

**Admin / ops**
```
POST /admin/sync            [ADMIN]   → triggers sync, returns run summary
GET  /admin/sync/runs       [ADMIN]   → recent sync_runs
GET  /health                          → { status, version }
```

- **Pagination:** offset for MVP; expose an optional `cursor` early so the contract is stable when we move to keyset pagination for large feeds (V1 shipped _no_ pagination and capped at 20 silently — designed out).
- **Response envelope** always `{ total, items, next_cursor }` for lists so the frontend can drive result counts and "load more" from real data (fixes V1 [I1]/[I2]).

---

## 10. Risks

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| **R1** | **Meetup/Luma scraping is fragile _and_ ToS/legal-sensitive.** Meetup removed its free API; both sites are JS-hydrated and actively change markup. This is the single biggest durability + legal risk in the product. | **High** | Prefer official/free APIs (Ticketmaster first). Label scraped sources. Rate-limit, cache, respect robots.txt, attribute source, deep-link out (don't re-host). **Get a legal read before launch.** Design providers to degrade to zero without breaking sync. |
| R2 | **Render free tier sleeps** → cold starts for the first user after idle. | Med | Accept for MVP; keep-warm ping or paid upgrade later. Don't put latency-critical UX on the free tier long-term. |
| R3 | **GitHub Actions cron is best-effort + auto-disables after 60d idle.** | Med | Monthly keepalive; consider Supabase `pg_cron`+`pg_net` as primary trigger, GH Actions as backup. Alert on missed sync via `sync_runs` freshness. |
| R4 | **Cross-provider dedup** over/under-merges duplicates. | Med | Heuristic hash + canonical grouping + `pg_trgm` fuzzy match; make it observable (review queue), not silent. |
| R5 | **Supabase JWT signing migration (HS256 → JWKS).** | Med | Build verifier against JWKS from day one; cache + refresh on `kid` miss. |
| R6 | **Free-tier ceilings** (Supabase row/egress, Render hours, GH minutes). | Med | Track usage; the architecture scales by swapping the _host_, not the _code_. |
| R7 | **Scraping IP bans** hit Render's shared egress. | Med | Backoff, jitter, realistic headers, low frequency (6h is friendly). Optionally a proxy later (cost). |
| R8 | **Secrets already committed** (`backend/.env` key, `venv/`, `eventmesh.db`). | High | Phase 0: rotate key, purge from tracking (and decide on history rewrite). Carried from V1. |
| R9 | **Native-event registration implies emails/notifications** users will expect (confirmations). | Low-Med | MVP: in-app only; wire Supabase/Resend email as fast-follow. Set expectations in UI. |
| R10 | **Recommendations/semantic search** scope-creep. | Low | Explicitly deferred (Phase 7); abstraction keeps it swappable. |

---

## 11. Trade-offs (decisions and what we're giving up)

1. **Modular monolith vs microservices** — chose monolith. Give up independent scaling/deploy per domain; gain drastically lower ops + cost. Right for this stage.
2. **Visible = view vs projection table** — chose view for MVP. Give up read-time denormalization speed; gain zero dual-write bugs. Revisit when search moves to Meilisearch.
3. **Service-role + app authz vs RLS-first** — leaning service-role for velocity, RLS as defense-in-depth. Give up automatic DB-level protection as the _primary_ guard; gain simpler session handling. Reversible if we enable RLS enforcement.
4. **GitHub Actions vs pg_cron for sync** — you chose GH Actions; I flag pg_cron as more reliable and equally free. Trade-off: GH Actions keeps orchestration in one visible place (the repo) vs pg_cron's reliability. **Open decision.**
5. **Scraping vs API breadth** — scraping buys Meetup/Luma coverage at the cost of fragility + legal exposure. We contain it behind the provider interface so its blast radius is one module.
6. **Lightened DDD vs full hexagonal** — chose lightened. Give up textbook purity; gain shipping speed. Provider + search boundaries stay strictly hexagonal where variability is real.
7. **Meilisearch later vs never** — **⚑ CTO CHALLENGE:** Meilisearch needs its own hosting (not trivially free long-term). **Postgres FTS + `pgvector` (both already in Supabase)** can likely serve _both_ "better search" and "semantic search" without adding infra. I'd keep the `SearchBackend` abstraction but **consider skipping Meilisearch entirely** and going SQL-FTS → pgvector. Flagging so we don't add a service we don't need.
8. **Offset vs cursor pagination** — offset now for simplicity, cursor field reserved in the contract. Give up nothing durable.

---

## 12. Detailed Implementation Roadmap

Each phase is independently shippable and reviewable. **No code is written until you approve the plan and answer §13.**

### Phase 0 — Foundations & Hygiene _(prereq, ~small)_
- Rotate the committed Eventbrite key; `git rm --cached` `backend/.env`, `backend/venv/`, `backend/eventmesh.db`; fix `.gitignore`. Decide history rewrite (§13 Q6).
- New backend scaffold: `pyproject.toml` (pinned), app factory, `core/` (config, db, logging, exceptions), Alembic baseline, `/health`.
- Provision Supabase project (prod + optional staging); wire `DATABASE_URL` (asyncpg).
- `ci.yml` (lint + test).
- **Deliverable:** clean repo, deployable empty API on Render, migrations run.

### Phase 1 — Auth & Identity
- `core/security.py` JWT verify via JWKS; `current_user` dep with JIT profile provisioning.
- `users` + `organizers` modules: `profiles`, `organizations`, `organization_members`, `organizer_follows` tables + `/me`, `/organizations`.
- Frontend: add `@supabase/supabase-js`, Google + OTP login, attach Bearer token to API calls.
- **Deliverable:** a user can log in (Google/OTP) and `GET /me` works end-to-end.

### Phase 2 — Read API & Frontend Integration
- `events` read module + `visible_events` view (native published + imported active) — imported side empty for now.
- `GET /events`, `GET /events/{kind}/{id}` with `{ total, items, next_cursor }`.
- Frontend integration (no redesign): env-driven `VITE_API_BASE_URL`, small API/query layer, add Tailwind, wire pagination + result counts + error/empty states (fixes V1 [I1]–[I5]).
- **Deliverable:** existing UI renders real API data with working filters + pagination.

### Phase 3 — Provider Framework & Sync
- `providers/base.py` + registry + normalizer + dedup; port Eventbrite (API + scrape fallback), Meetup (scrape), Luma (scrape); **wire Ticketmaster (API) early** per §5 challenge.
- `imported_events_raw`, `imported_events`, `sync_runs`; `sync.service` (fetch→normalize→validate→dedup→merge→store, fail-soft).
- `POST /admin/sync` (token) + `GET /admin/sync/runs`; `.github/workflows/sync.yml` cron 6h (+ evaluate pg_cron).
- **Deliverable:** aggregated events flow into `visible_events` on a 6-hour cadence; one provider failing doesn't stop the rest.

### Phase 4 — Native Events & Organizer Flow
- `native_events` + lifecycle (draft→preview→publish→cancel); organizer endpoints; publish surfaces into `visible_events`.
- `event_registrations` (native only) + register/cancel + organizer attendee list.
- Frontend: organizer create/preview/publish screens + register button (integration only).
- **Deliverable:** an organizer can host, publish, and collect registrations on EventMesh.

### Phase 5 — Engagement
- `saved_events` (both kinds) + follows UI; "my saved" / "following" feeds.
- **Deliverable:** save favourites + follow organizers, end-to-end.

### Phase 6 — Search Abstraction (SQL)
- `SearchBackend` Protocol + `sql_backend` (Postgres FTS, `pg_trgm`); `/search` behind the abstraction; frontend never touches SQL semantics.
- **Deliverable:** real search/filter with a swappable backend.

### Phase 7 — Advanced Search & Recommendations _(deferred)_
- Evaluate **pgvector on Supabase** for semantic search (vs standing up Meilisearch — see §11.7). Embeddings pipeline; simple recommendations (saved/followed/category affinity).
- **Deliverable:** semantic search + first-cut recommendations, no new infra if pgvector suffices.

---

## 13. Open Questions (need answers before Phase 0)

1. **Search infra:** OK to **skip Meilisearch** and go SQL-FTS → `pgvector` (both free on Supabase), keeping the abstraction? Or is Meilisearch a hard requirement?
2. **Sync trigger:** GitHub Actions as specified, or make **Supabase `pg_cron`** the primary (more reliable, equally free) with GH Actions as backup?
3. **Trust boundary:** service-role + app authz (velocity) vs RLS-first (defense-in-depth) as the _primary_ guard? This changes DB session wiring in Phase 1.
4. **Ticketmaster sequencing:** bring it into Phase 3's first sync (official, free, stable) rather than deferring? I strongly recommend yes.
5. **Meetup/Luma scraping:** are you comfortable with the **ToS/legal exposure** (R1), or should aggregation launch **API-only** (Eventbrite + Ticketmaster) with scraping gated behind a legal review?
6. **Git history:** full rewrite (`git filter-repo`) to purge the committed secret/DB/`venv`, or stop-tracking-going-forward only?
7. **DDD depth:** accept the lightened modular layout (§2), or do you want strict per-module `domain/application/infrastructure`?
8. **Render cold starts (R2):** acceptable for MVP launch, or should we plan a keep-warm/alternative host from day one?

---

_No code has been modified. Review §11 trade-offs and answer §13, then tell me which phases to start. I'll treat any of the ⚑ CTO CHALLENGE items you reject as settled and proceed with your original decision._
