"""Meetup provider — scrapes each requested city's Meetup 'find' page."""

from app.modules.providers.base import BaseProvider, FetchContext, NormalizedEvent, ProviderMeta
from app.modules.providers.meetup.client import MeetupClient
from app.modules.providers.meetup.mapper import to_normalized
from app.modules.providers.meetup.scraper import parse_events

# Meetup uses slugged locations; fall back to a naive slug for unknown cities.
_CITY_SLUGS = {
    "San Francisco": "us--ca--san-francisco",
    "London": "gb--eng--london",
    "New York": "us--ny--new-york",
    "Bangalore": "in--bangalore",
    "Berlin": "de--berlin",
}


def _find_url(city: str) -> str:
    slug = _CITY_SLUGS.get(city) or city.lower().replace(" ", "-")
    return f"https://www.meetup.com/find/?location={slug}&source=EVENTS"


class MeetupProvider(BaseProvider):
    meta = ProviderMeta(slug="meetup", display_name="Meetup", kind="scrape", enabled=True)

    def __init__(self, *, client: MeetupClient | None = None) -> None:
        self._client = client

    def _make_client(self) -> MeetupClient:
        return self._client if self._client is not None else MeetupClient()

    async def fetch(self, ctx: FetchContext) -> list[dict]:
        client = self._make_client()
        events: list[dict] = []
        async with client:
            for city in ctx.cities:
                try:
                    html = await client.get_html(_find_url(city))
                except Exception:  # noqa: BLE001 - one city failing must not kill the rest
                    continue
                for raw in parse_events(html):
                    raw["_city"] = city
                    events.append(raw)
        return events

    def normalize(self, raw: dict) -> NormalizedEvent | None:
        return to_normalized(raw, raw.get("_city"))
