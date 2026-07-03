"""Search abstraction.

The API depends on ``SearchBackend``, never on SQL directly, so the engine can
move from Postgres full-text search (MVP) to pgvector semantic search later
without touching callers. The concrete Postgres backend lands in ``sql_backend``.
"""

from __future__ import annotations

from typing import Literal, Protocol

from pydantic import BaseModel

DateRange = Literal["all", "today", "week", "month"]


class SearchQuery(BaseModel):
    """A discovery query over the visible read model.

    Every field is optional so the same shape serves both plain browse (no ``q``,
    ordered by soonest) and relevance search (``q`` set, ordered by rank). The
    view already constrains results to canonical, active, future events; these
    filters narrow further.
    """

    q: str | None = None
    city: str | None = None
    category: str | None = None
    source: str | None = None  # provider slug: eventmesh | eventbrite | meetup | luma
    is_free: bool | None = None
    is_online: bool | None = None
    date_range: DateRange = "all"
    limit: int = 20
    offset: int = 0

    @property
    def has_query(self) -> bool:
        return bool(self.q and self.q.strip())


class SearchBackend(Protocol):
    async def search(self, query: SearchQuery) -> dict:
        """Return {'total': int, 'items': list[dict]} for the given query."""
        ...
