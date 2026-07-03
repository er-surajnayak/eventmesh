"""Discovery search service — the seam the API depends on.

Callers hand it a ``SearchQuery`` and get a ``{total, items}`` result. The
concrete engine (Postgres FTS today, pgvector later) is injected, so swapping
backends never touches the router.
"""

from __future__ import annotations

from app.modules.search.base import SearchBackend, SearchQuery


class SearchService:
    def __init__(self, backend: SearchBackend) -> None:
        self._backend = backend

    async def search(self, query: SearchQuery) -> dict:
        return await self._backend.search(query)
