"""search vector on visible_events + FTS/trigram/feed indexes

Phase 5A. Adds a ``search_vector`` column to the visible_events VIEW and the
matching index infrastructure so discovery search and browse are index-backed:

* GIN full-text indexes on native_events/imported_events using the *same*
  tsvector expression the view exposes, so ``search_vector @@ tsquery`` on the
  view is planned against the base-table indexes.
* pg_trgm trigram indexes on title for fuzzy/ILIKE acceleration (future use).
* btree feed indexes matching the view's filter+order (start_time) so plain
  soonest-first browse is index-backed too.

Revision ID: b7c1f9e2a4d0
Revises: 313406be2548
Create Date: 2026-07-04 00:00:00.000000+00:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "b7c1f9e2a4d0"
down_revision: str | None = "313406be2548"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# The tsvector expressions MUST be byte-identical to the ones used by the GIN
# indexes below, or Postgres won't use the indexes for the view's predicate.
_NATIVE_TSV = (
    "to_tsvector('english', "
    "coalesce(ne.title, '') || ' ' || coalesce(ne.description, '') || ' ' || "
    "coalesce(ne.city, '') || ' ' || coalesce(ne.venue_name, ''))"
)
_IMPORTED_TSV = (
    "to_tsvector('english', "
    "coalesce(ie.title, '') || ' ' || coalesce(ie.description, '') || ' ' || "
    "coalesce(ie.city, '') || ' ' || coalesce(ie.venue, ''))"
)

# visible_events with search_vector appended (CREATE OR REPLACE allows adding
# trailing columns; leading columns are unchanged from 313406be2548).
_VIEW_WITH_SEARCH = f"""
CREATE OR REPLACE VIEW visible_events AS
SELECT
    'native'::text                       AS kind,
    ne.id                                AS id,
    ne.slug::text                        AS slug,
    ne.title::text                       AS title,
    ne.description                       AS description,
    ne.cover_image_url::text             AS image_url,
    ne.start_time                        AS start_time,
    ne.end_time                          AS end_time,
    ne.timezone::text                    AS timezone,
    ne.city::text                        AS city,
    ne.venue_name::text                  AS venue,
    (ne.event_type = 'online')           AS is_online,
    ne.is_free                           AS is_free,
    ne.price_cents                       AS price_cents,
    ne.currency::text                    AS currency,
    NULL::text                           AS category,
    NULL::text                           AS url,
    'eventmesh'::text                    AS provider,
    ARRAY['eventmesh']::text[]           AS sources,
    ne.organization_id                   AS organization_id,
    {_NATIVE_TSV}                        AS search_vector
FROM native_events ne
WHERE ne.status = 'published'
  AND ne.visibility = 'public'
  AND ne.start_time > now()
UNION ALL
SELECT
    'imported'::text                     AS kind,
    ie.id                                AS id,
    NULL::text                           AS slug,
    ie.title::text                       AS title,
    ie.description                       AS description,
    ie.image_url::text                   AS image_url,
    ie.start_time                        AS start_time,
    ie.end_time                          AS end_time,
    ie.timezone::text                    AS timezone,
    ie.city::text                        AS city,
    ie.venue::text                       AS venue,
    ie.is_online                         AS is_online,
    ie.is_free                           AS is_free,
    ie.price_cents                       AS price_cents,
    ie.currency::text                    AS currency,
    ie.category::text                    AS category,
    ie.url::text                         AS url,
    ie.provider::text                    AS provider,
    (SELECT array_agg(DISTINCT i2.provider::text ORDER BY i2.provider::text)
       FROM imported_events i2
      WHERE i2.canonical_group_id = ie.canonical_group_id
        AND i2.status = 'active')        AS sources,
    NULL::uuid                           AS organization_id,
    {_IMPORTED_TSV}                      AS search_vector
FROM imported_events ie
WHERE ie.is_canonical = true
  AND ie.status = 'active'
  AND ie.start_time > now();
"""

# The original view (no search_vector) for downgrade.
_VIEW_ORIGINAL = """
CREATE OR REPLACE VIEW visible_events AS
SELECT
    'native'::text                       AS kind,
    ne.id                                AS id,
    ne.slug::text                        AS slug,
    ne.title::text                       AS title,
    ne.description                       AS description,
    ne.cover_image_url::text             AS image_url,
    ne.start_time                        AS start_time,
    ne.end_time                          AS end_time,
    ne.timezone::text                    AS timezone,
    ne.city::text                        AS city,
    ne.venue_name::text                  AS venue,
    (ne.event_type = 'online')           AS is_online,
    ne.is_free                           AS is_free,
    ne.price_cents                       AS price_cents,
    ne.currency::text                    AS currency,
    NULL::text                           AS category,
    NULL::text                           AS url,
    'eventmesh'::text                    AS provider,
    ARRAY['eventmesh']::text[]           AS sources,
    ne.organization_id                   AS organization_id
FROM native_events ne
WHERE ne.status = 'published'
  AND ne.visibility = 'public'
  AND ne.start_time > now()
UNION ALL
SELECT
    'imported'::text                     AS kind,
    ie.id                                AS id,
    NULL::text                           AS slug,
    ie.title::text                       AS title,
    ie.description                       AS description,
    ie.image_url::text                   AS image_url,
    ie.start_time                        AS start_time,
    ie.end_time                          AS end_time,
    ie.timezone::text                    AS timezone,
    ie.city::text                        AS city,
    ie.venue::text                       AS venue,
    ie.is_online                         AS is_online,
    ie.is_free                           AS is_free,
    ie.price_cents                       AS price_cents,
    ie.currency::text                    AS currency,
    ie.category::text                    AS category,
    ie.url::text                         AS url,
    ie.provider::text                    AS provider,
    (SELECT array_agg(DISTINCT i2.provider::text ORDER BY i2.provider::text)
       FROM imported_events i2
      WHERE i2.canonical_group_id = ie.canonical_group_id
        AND i2.status = 'active')        AS sources,
    NULL::uuid                           AS organization_id
FROM imported_events ie
WHERE ie.is_canonical = true
  AND ie.status = 'active'
  AND ie.start_time > now();
"""

_NATIVE_TSV_INDEX = _NATIVE_TSV.replace("ne.", "")
_IMPORTED_TSV_INDEX = _IMPORTED_TSV.replace("ie.", "")

_INDEXES = [
    "CREATE INDEX IF NOT EXISTS ix_native_events_search "
    f"ON native_events USING gin ({_NATIVE_TSV_INDEX})",
    "CREATE INDEX IF NOT EXISTS ix_imported_events_search "
    f"ON imported_events USING gin ({_IMPORTED_TSV_INDEX})",
    "CREATE INDEX IF NOT EXISTS ix_native_events_title_trgm "
    "ON native_events USING gin (title gin_trgm_ops)",
    "CREATE INDEX IF NOT EXISTS ix_imported_events_title_trgm "
    "ON imported_events USING gin (title gin_trgm_ops)",
    # Feed ordering/filtering (soonest-first browse over the view branches).
    "CREATE INDEX IF NOT EXISTS ix_native_events_feed "
    "ON native_events (status, visibility, start_time)",
    "CREATE INDEX IF NOT EXISTS ix_imported_events_feed "
    "ON imported_events (is_canonical, status, start_time)",
]

_INDEX_NAMES = [
    "ix_native_events_search",
    "ix_imported_events_search",
    "ix_native_events_title_trgm",
    "ix_imported_events_title_trgm",
    "ix_native_events_feed",
    "ix_imported_events_feed",
]


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute(_VIEW_WITH_SEARCH)
    for stmt in _INDEXES:
        op.execute(stmt)


def downgrade() -> None:
    for name in _INDEX_NAMES:
        op.execute(f"DROP INDEX IF EXISTS {name}")
    # CREATE OR REPLACE cannot drop the search_vector column; drop then recreate.
    op.execute("DROP VIEW IF EXISTS visible_events")
    op.execute(_VIEW_ORIGINAL)
    # pg_trgm is left installed — it is cheap and may be relied on elsewhere.
