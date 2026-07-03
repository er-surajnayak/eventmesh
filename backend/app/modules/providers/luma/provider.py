"""Luma provider — scrapes each requested city's Luma page (structured-data first)."""

from app.modules.providers.base import BaseProvider, FetchContext, NormalizedEvent, ProviderMeta
from app.modules.providers.luma.mapper import to_normalized
from app.modules.providers.luma.scraper import parse_events
from app.modules.providers.scrape_client import ScrapeClient

_CITY_SLUGS = {
    "San Francisco": "sf",
    "New York": "nyc",
    "London": "london",
    "Bangalore": "bangalore",
    "Berlin": "berlin",
}


def _city_url(city: str) -> str:
    slug = _CITY_SLUGS.get(city) or city.lower().replace(" ", "-")
    return f"https://lu.ma/{slug}"


class LumaProvider(BaseProvider):
    meta = ProviderMeta(slug="luma", display_name="Luma", kind="scrape", enabled=True)

    def __init__(self, *, client: ScrapeClient | None = None) -> None:
        self._client = client

    def _make_client(self) -> ScrapeClient:
        return self._client if self._client is not None else ScrapeClient(source="luma")

    async def fetch(self, ctx: FetchContext) -> list[dict]:
        client = self._make_client()
        events: list[dict] = []
        async with client:
            for city in ctx.cities:
                try:
                    html = await client.get_html(_city_url(city))
                except Exception:  # noqa: BLE001 - one city failing must not kill the rest
                    continue
                for raw in parse_events(html):
                    raw["_city"] = city
                    events.append(raw)
        return events

    def normalize(self, raw: dict) -> NormalizedEvent | None:
        return to_normalized(raw, raw.get("_city"))
