"""Search abstraction.

The API depends on ``SearchBackend``, never on SQL directly, so the engine can
move from Postgres full-text search (MVP) to pgvector semantic search later
without touching callers. Concrete backends land in Phase 5.
"""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel


class SearchQuery(BaseModel):
    q: str | None = None
    city: str | None = None
    category: str | None = None
    is_free: bool | None = None
    is_online: bool | None = None
    limit: int = 20
    offset: int = 0


class SearchBackend(Protocol):
    async def search(self, query: SearchQuery) -> dict:
        """Return {'total': int, 'items': list[...]} for the given query."""
        ...
