"""visible events view

Revision ID: 313406be2548
Revises: f4ddd2bc71be
Create Date: 2026-07-03 19:25:10.170110+00:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "313406be2548"
down_revision: str | None = "f4ddd2bc71be"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Visible read model: published/public native events + canonical, active, future
# imported events. Imported records stay internal — only the canonical surfaces,
# with a `sources` array preserving provenance. Rebuild this migration to change
# the projection (CREATE OR REPLACE keeps it simple).
_VIEW_SQL = """
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


def upgrade() -> None:
    op.execute(_VIEW_SQL)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS visible_events")
