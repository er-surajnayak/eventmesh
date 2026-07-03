"""Eventbrite provider.

The official v3 API no longer offers public city search, so we aggregate the
token owner's organizations' live events (with venue expanded), paginating each.
"""

from app.core.config import settings
from app.modules.providers.base import BaseProvider, FetchContext, NormalizedEvent, ProviderMeta
from app.modules.providers.eventbrite.client import EventbriteClient
from app.modules.providers.eventbrite.mapper import to_normalized


class EventbriteProvider(BaseProvider):
    meta = ProviderMeta(slug="eventbrite", display_name="Eventbrite", kind="api", enabled=True)

    def __init__(self, *, client: EventbriteClient | None = None) -> None:
        self._client = client

    def _make_client(self) -> EventbriteClient:
        if self._client is not None:
            return self._client
        return EventbriteClient(settings.eventbrite_api_key or "", settings.eventbrite_api_base)

    async def fetch(self, ctx: FetchContext) -> list[dict]:
        client = self._make_client()
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

    def normalize(self, raw: dict) -> NormalizedEvent | None:
        return to_normalized(raw)
