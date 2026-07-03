"""Postgres full-text search over the ``visible_events`` read model.

This is the MVP ``SearchBackend``. It queries the view (native published +
canonical/active/future imported), so it never touches provider-specific rows.
Relevance uses Postgres FTS (``websearch_to_tsquery`` + ``ts_rank_cd``) against
the view's ``search_vector`` column, which is index-backed on the base tables
(see the Phase 5A migration). When no query text is given it degrades to a plain
browse ordered by soonest start.

The query-building helpers are pure functions (no DB, no I/O) so filter and
ordering logic is unit-testable, matching the rest of the suite.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.search.base import SearchQuery

# Columns exposed by the visible_events VIEW (search_vector is used only for
# filtering/ranking, never returned).
_COLUMNS = (
    "kind, id, slug, title, description, image_url, start_time, end_time, timezone, "
    "city, venue, is_online, is_free, price_cents, currency, category, url, provider, "
    "sources, organization_id"
)

# Upper bound (exclusive) per date_range window. The view already enforces the
# lower bound (start_time > now()); these only cap how far ahead to look. Using
# SQL now() keeps the window consistent with the view.
_DATE_UPPER_BOUND: dict[str, str] = {
    "today": "date_trunc('day', now()) + interval '1 day'",
    "week": "now() + interval '7 days'",
    "month": "now() + interval '30 days'",
}


def build_where(query: SearchQuery) -> tuple[list[str], dict]:
    """Translate a query into SQL WHERE clauses + bound params (pure)."""
    clauses: list[str] = []
    params: dict = {}

    if query.has_query:
        clauses.append("search_vector @@ websearch_to_tsquery('english', :q)")
        params["q"] = query.q.strip()
    if query.city:
        clauses.append("lower(city) = lower(:city)")
        params["city"] = query.city
    if query.category:
        clauses.append("lower(category) = lower(:category)")
        params["category"] = query.category
    if query.source:
        clauses.append("provider = :source")
        params["source"] = query.source
    if query.is_free is not None:
        clauses.append("is_free = :is_free")
        params["is_free"] = query.is_free
    if query.is_online is not None:
        clauses.append("is_online = :is_online")
        params["is_online"] = query.is_online

    upper = _DATE_UPPER_BOUND.get(query.date_range)
    if upper:
        clauses.append(f"start_time < {upper}")

    return clauses, params


def order_by(has_query: bool) -> str:
    """Rank by relevance when searching; otherwise soonest-first browse."""
    if has_query:
        return (
            "ORDER BY ts_rank_cd(search_vector, websearch_to_tsquery('english', :q)) "
            "DESC, start_time ASC"
        )
    return "ORDER BY start_time ASC"


class SqlSearchBackend:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def search(self, query: SearchQuery) -> dict:
        clauses, params = build_where(query)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        total = (
            await self._db.execute(text(f"SELECT count(*) FROM visible_events {where}"), params)
        ).scalar() or 0

        page_params = {**params, "limit": query.limit, "offset": query.offset}
        rows = (
            (
                await self._db.execute(
                    text(
                        f"SELECT {_COLUMNS} FROM visible_events {where} "
                        f"{order_by(query.has_query)} LIMIT :limit OFFSET :offset"
                    ),
                    page_params,
                )
            )
            .mappings()
            .all()
        )
        return {"total": total, "items": [dict(r) for r in rows]}
