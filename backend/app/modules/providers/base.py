"""Provider framework — the seam that hides transport (API/GraphQL/scrape/RSS).

Concrete providers (Eventbrite/Meetup/Luma) subclass ``BaseProvider`` and only
implement ``fetch`` + ``normalize``; the ``sync`` template handles validation and
per-provider metric collection. Everything downstream sees ``NormalizedEvent``.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

ProviderKind = Literal["api", "graphql", "scrape", "rss"]


class ProviderMeta(BaseModel):
    slug: str
    display_name: str
    kind: ProviderKind
    enabled: bool = True
    ratelimit_per_min: int = 30


class FetchContext(BaseModel):
    cities: list[str] = []


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


class ProviderSyncResult(BaseModel):
    fetched: int
    events: list[NormalizedEvent]
    errors: list[str] = []


class BaseProvider(ABC):
    """Template-method base. Subclasses set ``meta`` and implement fetch/normalize."""

    meta: ProviderMeta

    @abstractmethod
    async def fetch(self, ctx: FetchContext) -> list[dict]:
        """Retrieve raw upstream payloads (one dict per event)."""

    @abstractmethod
    def normalize(self, raw: dict) -> NormalizedEvent | None:
        """Map one raw payload to a NormalizedEvent, or None if unmappable."""

    def validate(self, event: NormalizedEvent) -> bool:
        """Minimum bar to be storable. Providers may override to be stricter."""
        return bool(event.title and event.url and event.external_id and event.start_time)

    async def sync(self, ctx: FetchContext) -> ProviderSyncResult:
        """fetch → normalize → validate, collecting errors (never raising per-item)."""
        raws = await self.fetch(ctx)
        events: list[NormalizedEvent] = []
        errors: list[str] = []
        for raw in raws:
            try:
                event = self.normalize(raw)
            except Exception as exc:  # noqa: BLE001 - one bad item must not kill the batch
                errors.append(f"normalize error: {exc}")
                continue
            if event is None:
                continue
            if self.validate(event):
                events.append(event)
            else:
                errors.append(f"invalid event: {event.external_id or event.url}")
        return ProviderSyncResult(fetched=len(raws), events=events, errors=errors)
