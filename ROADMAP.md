# EventMesh — Roadmap

## Completed

- ✅ **Phase 0 — Foundations & Deployment**: scaffold, config, Docker, Alembic,
  Supabase, Render, GitHub Actions, health, CI.
- ✅ **Phase 1 — Authentication**: Supabase JWKS, Google + Email OTP, protected
  routes, profile/auth separation, frontend integration.
- ✅ **Phase 2 — Identity & Organizations**: profiles/roles, organizations +
  multi-member membership, become-organizer, slugs, org status/type, authz.
- ✅ **Phase 3 — Event Management**:
  - 3A: native event model + CRUD.
  - 3B: lifecycle state machine, registration + capacity/waitlist, visibility,
    public browsing.
  - 3C: organizer experience — dashboard (Draft/Published/Archived tabs, analytics
    placeholders), multi-step wizard with draft autosave, preview/publish.
- ✅ **Phase 4 — Event Aggregation Engine**:
  - 4A framework/dedup/sync-report infra · 4B Eventbrite (API) · 4C Meetup
    (scrape) · 4D Luma (scrape) · 4E merge engine + canonical + `visible_events`
    VIEW + public `GET /events` feed.

## Next

### Phase 5 — Discovery Platform (was "Search")
Turn the live aggregation feed into a great public discovery experience. Focus:
- **Search UX** — query, relevance, empty/loading states, over the visible read
  model (Postgres FTS first; keep the `SearchService` abstraction for pgvector).
- **Filters** — city, date range, free/paid, online/in-person, category, source.
- **Discovery** — curated/trending/near-you surfaces, source strip, pagination /
  infinite scroll.
- **SEO** — SSR/meta/OpenGraph for event + discovery pages, sitemap, canonical
  URLs, structured data (schema.org Event).
- **Performance** — query indexing on `visible_events`/`imported_events`, caching,
  bundle/image optimization, Render cold-start mitigation.
- **Public event browsing** — wire the frontend to `GET /api/v1/events` (replace
  the legacy/static landing feed), deep-link imported events to source, native to
  `/events/{slug}`.

_Prerequisite housekeeping to consider early in Phase 5: valid Eventbrite token;
confirm browser CORS/login on eventmesh.xyz; add indexes for the visible feed._

### Later (architecture-ready, not built)
- Payments / ticketing / QR check-in.
- Notifications delivery (module scaffolded).
- Semantic search (pgvector), AI recommendations.
- Analytics (dashboard placeholders exist).
- Imported-event retention job (archive on completion, delete after 90 days).
- Waitlist auto-promotion; RLS enforcement; git-history rewrite before public
  launch; additional providers (Devfolio, Townscript, Ticketmaster).
