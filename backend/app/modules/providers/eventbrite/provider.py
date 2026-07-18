"""Eventbrite provider: official API plus bounded public HTML discovery.

The official v3 API only exposes events owned by organizations available to the
token; it no longer provides public city search. Authorized organization events
remain API-backed, while public discovery uses one server-rendered city listing
request per configured city. Both paths emit the same API-shaped raw payload so
normalization and downstream canonicalization remain unchanged.
"""

from app.core.config import settings
from app.core.logging import get_logger
from app.modules.providers.base import (
    BaseProvider,
    FetchContext,
    NormalizedEvent,
    ProviderMeta,
    ProviderSyncResult,
)
from app.modules.providers.eventbrite.client import EventbriteClient
from app.modules.providers.eventbrite.mapper import to_normalized
from app.modules.providers.eventbrite.scraper import parse_events
from app.modules.providers.scrape_client import ScrapeClient

logger = get_logger(__name__)

_CITY_SLUGS = {
    "Mumbai": "india--mumbai",
    "Bangalore": "india--bangalore",
    "Delhi NCR": "india--new-delhi",
    "Hyderabad": "india--hyderabad",
    "Chennai": "india--chennai",
    "Pune": "india--pune",
    "Kolkata": "india--kolkata",
    "Ahmedabad": "india--ahmedabad",
    "Jaipur": "india--jaipur",
    "Kochi": "india--kochi",
    "Goa": "india--goa",
    "Chandigarh": "india--chandigarh",
    "Indore": "india--indore",
    "Lucknow": "india--lucknow",
    "Surat": "india--surat",
    "Nagpur": "india--nagpur",
    "Bhubaneswar": "india--bhubaneswar",
    "Singapore": "singapore--singapore",
    "Dubai": "united-arab-emirates--dubai",
    "London": "united-kingdom--london",
    "Berlin": "germany--berlin",
    "New York": "ny--new-york",
    "San Francisco": "ca--san-francisco",
}


def _city_url(city: str) -> str | None:
    slug = _CITY_SLUGS.get(city)
    return f"https://www.eventbrite.com/d/{slug}/events/" if slug else None


class EventbriteProvider(BaseProvider):
    meta = ProviderMeta(slug="eventbrite", display_name="Eventbrite", kind="hybrid", enabled=True)

    def __init__(
        self,
        *,
        client: EventbriteClient | None = None,
        scrape_client: ScrapeClient | None = None,
        api_enabled: bool = True,
        scrape_enabled: bool = True,
    ) -> None:
        self._client = client
        self._scrape_client = scrape_client
        self._api_enabled = api_enabled
        self._scrape_enabled = scrape_enabled
        self._fetch_errors: list[str] = []

    def _make_client(self) -> EventbriteClient | None:
        if not self._api_enabled:
            return None
        if self._client is not None:
            return self._client
        if not settings.eventbrite_api_key:
            return None
        return EventbriteClient(settings.eventbrite_api_key, settings.eventbrite_api_base)

    def _make_scrape_client(self) -> ScrapeClient:
        if self._scrape_client is not None:
            return self._scrape_client
        return ScrapeClient(source="eventbrite")

    async def _fetch_owned_events(self) -> list[dict]:
        client = self._make_client()
        if client is None:
            return []

        async with client:
            organizations = await client.paginate("/users/me/organizations/", {}, "organizations")
            events: list[dict] = []
            for org in organizations:
                org_id = org.get("id")
                if not org_id:
                    continue
                events.extend(
                    await client.paginate(
                        f"/organizations/{org_id}/events/",
                        {"status": "live", "expand": "venue", "order_by": "start_asc"},
                        "events",
                    )
                )
            return events

    async def _fetch_public_events(self, ctx: FetchContext) -> list[dict]:
        if not self._scrape_enabled or not ctx.cities:
            return []

        client = self._make_scrape_client()
        events: list[dict] = []
        async with client:
            for city in ctx.cities:
                url = _city_url(city)
                if url is None:
                    self._fetch_errors.append(f"unsupported Eventbrite city: {city}")
                    continue
                try:
                    html = await client.get_html(url)
                    events.extend(parse_events(html, fallback_city=city))
                except Exception as exc:  # noqa: BLE001 - one city must not abort the provider
                    logger.warning("eventbrite_scrape_failed", city=city, error=str(exc))
                    self._fetch_errors.append(f"Eventbrite scrape failed for {city}: {exc}")
        return events

    async def fetch(self, ctx: FetchContext) -> list[dict]:
        self._fetch_errors = []
        try:
            api_events = await self._fetch_owned_events()
        except Exception as exc:  # noqa: BLE001 - public fallback must remain available
            logger.warning("eventbrite_api_failed", error=str(exc))
            self._fetch_errors.append(f"Eventbrite API failed: {exc}")
            api_events = []

        scraped_events = await self._fetch_public_events(ctx)

        # The same owned event may also appear in a city listing. Prefer the API
        # representation and keep insertion order deterministic.
        unique: list[dict] = []
        seen: set[str] = set()
        for raw in [*api_events, *scraped_events]:
            key = str(raw.get("id") or raw.get("url") or "")
            if not key or key in seen:
                continue
            seen.add(key)
            unique.append(raw)
        return unique

    async def sync(self, ctx: FetchContext) -> ProviderSyncResult:
        result = await super().sync(ctx)
        if not self._fetch_errors:
            return result
        return result.model_copy(update={"errors": [*self._fetch_errors, *result.errors]})

    def normalize(self, raw: dict) -> NormalizedEvent | None:
        return to_normalized(raw)
