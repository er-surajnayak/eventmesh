"""Provider interface — the seam that hides transport (API/GraphQL/scrape/RSS).

Nothing downstream of a provider knows how it fetched data. Every provider
returns the same ``NormalizedEvent``. Concrete providers (Eventbrite, Meetup,
Luma) are implemented in Phase 4; this module defines the contract only.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Protocol, runtime_checkable

from pydantic import BaseModel

ProviderKind = Literal["api", "graphql", "scrape", "rss"]


class ProviderMeta(BaseModel):
    slug: str
    display_name: str
    kind: ProviderKind
    enabled: bool = True
    ratelimit_per_min: int = 30


class NormalizedEvent(BaseModel):
    """The single normalized shape every provider maps into."""

    provider: str
    external_id: str
    url: str
    title: str
    description: str | None = None
    image_url: str | None = None
    start_time: datetime
    end_time: datetime | None = None
    timezone: str | None = None
    city: str | None = None
    venue: str | None = None
    is_online: bool = False
    is_free: bool = True
    price_cents: int | None = None
    currency: str | None = None
    category: str | None = None


class FetchContext(BaseModel):
    """Inputs for a fetch run (cities, time window, etc.)."""

    cities: list[str] = []


@runtime_checkable
class EventProvider(Protocol):
    """The contract every source implements. Transport-agnostic by design."""

    meta: ProviderMeta

    async def fetch(self, ctx: FetchContext) -> list[dict]:
        """Retrieve raw upstream payloads."""
        ...

    def normalize(self, raw: dict) -> NormalizedEvent:
        """Map one raw payload into the normalized model."""
        ...

    def validate(self, event: NormalizedEvent) -> bool:
        """Return True if the normalized event is complete enough to store."""
        ...

    async def sync(self, ctx: FetchContext) -> list[NormalizedEvent]:
        """fetch -> normalize -> validate, returning storable events."""
        ...
