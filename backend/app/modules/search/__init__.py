"""Search domain: SearchService over a swappable backend.

Postgres FTS today (``SqlSearchBackend``), pgvector semantic search later — the
router only ever sees ``SearchService`` (Phase 5A).
"""
