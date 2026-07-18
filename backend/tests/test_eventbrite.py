"""Eventbrite connector tests — all responses mocked (no live API)."""

import httpx
import pytest

from app.modules.providers.base import FetchContext
from app.modules.providers.eventbrite.client import EventbriteClient
from app.modules.providers.eventbrite.mapper import to_normalized
from app.modules.providers.eventbrite.provider import EventbriteProvider
from app.modules.providers.eventbrite.scraper import parse_events
from app.modules.providers.scrape_client import ScrapeClient

BASE = "https://api.test/v3"

RAW_EVENT = {
    "id": "123",
    "name": {"text": "Tech Talk"},
    "description": {"text": "A talk about things"},
    "url": "https://eventbrite.com/e/123",
    "start": {"utc": "2027-03-01T18:00:00Z", "timezone": "America/Los_Angeles"},
    "end": {"utc": "2027-03-01T20:00:00Z"},
    "is_free": True,
    "online_event": False,
    "currency": "USD",
    "logo": {"url": "https://img/1.jpg"},
    "venue": {"name": "Hall A", "address": {"city": "San Francisco"}},
}

SERVER_DATA_HTML = """
<html><body>
<a data-event-id="456" data-event-paid-status="free"></a>
<script>
window.__SERVER_DATA__ = {
  "buckets": [{"events": [{
    "_type": "destination_event",
    "id": "456",
    "eventbrite_event_id": "456",
    "name": "Bengaluru Founder Night",
    "url": "https://www.eventbrite.com/e/founder-night-tickets-456?aff=city",
    "summary": "Meet local founders",
    "start_date": "2027-08-01",
    "start_time": "18:30",
    "end_date": "2027-08-01",
    "end_time": "20:00",
    "timezone": "Asia/Kolkata",
    "is_online_event": false,
    "image": {"url": "https://img/founders.jpg"},
    "primary_venue": {"name": "Tech Park", "address": {"city": "Bengaluru"}},
    "tags": [{"prefix": "EventbriteCategory", "display_name": "Business"}]
  }]}, {"duplicate": [{
    "_type": "destination_event", "id": "456", "name": "duplicate"
  }]}]
};
</script>
</body></html>
"""

JSON_LD_HTML = """
<html><head><script type="application/ld+json">
{"@context":"https://schema.org","@type":"ItemList","itemListElement":[
  {"@type":"ListItem","item":{"@type":"Event","name":"Design Conference",
   "url":"https://www.eventbrite.com/e/design-conf-tickets-789",
   "startDate":"2027-09-02T09:00:00+01:00","endDate":"2027-09-02T17:00:00+01:00",
   "description":"A design event","image":"https://img/design.jpg",
   "location":{"@type":"Place","name":"Design Hall","address":{"addressLocality":"London"}},
   "offers":{"@type":"Offer","price":"25","priceCurrency":"GBP"}}}
]}
</script></head></html>
"""


def _client(handler) -> EventbriteClient:
    http = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url=BASE)
    return EventbriteClient("token", BASE, client=http, backoff_base=0.001)


def _scrape_client(handler) -> ScrapeClient:
    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return ScrapeClient(client=http, min_delay=0, backoff_base=0.001, source="eventbrite")


# ── mapper ──────────────────────────────────────────────────────────


def test_mapper_maps_all_fields():
    ev = to_normalized(RAW_EVENT)
    assert ev is not None
    assert ev.provider == "eventbrite"
    assert ev.external_id == "123"
    assert ev.title == "Tech Talk"
    assert ev.city == "San Francisco"
    assert ev.venue == "Hall A"
    assert ev.is_free is True
    assert ev.timezone == "America/Los_Angeles"
    assert ev.start_time.year == 2027


def test_mapper_maps_category():
    raw = {**RAW_EVENT, "category": {"short_name": "Technology"}}
    assert to_normalized(raw).category == "Technology"


def test_mapper_returns_none_when_missing_essentials():
    assert to_normalized({"id": "1", "name": {"text": "No date"}}) is None


# ── scraper ─────────────────────────────────────────────────────────


def test_scraper_prefers_server_data_and_deduplicates():
    events = parse_events(SERVER_DATA_HTML, fallback_city="Bangalore")
    assert len(events) == 1
    raw = events[0]
    assert raw["id"] == "456"
    assert raw["start"]["utc"] == "2027-08-01T13:00:00Z"
    assert raw["end"]["utc"] == "2027-08-01T14:30:00Z"
    assert raw["start"]["timezone"] == "Asia/Kolkata"
    assert raw["venue"]["address"]["city"] == "Bengaluru"
    assert raw["is_free"] is True
    assert raw["category"]["short_name"] == "Business"
    assert raw["url"] == "https://www.eventbrite.com/e/founder-night-tickets-456"


def test_scraper_falls_back_to_json_ld():
    events = parse_events(JSON_LD_HTML, fallback_city="London")
    assert len(events) == 1
    raw = events[0]
    assert raw["id"] == "789"
    assert raw["start"]["utc"] == "2027-09-02T09:00:00+01:00"
    assert raw["venue"]["name"] == "Design Hall"
    assert raw["is_free"] is False
    assert raw["currency"] == "GBP"


def test_scraper_handles_empty_or_malformed_html():
    assert parse_events("<html><body>nothing</body></html>") == []
    assert parse_events("<script>window.__SERVER_DATA__ = {bad</script>") == []


# ── client: pagination ──────────────────────────────────────────────


async def test_client_paginates_via_continuation():
    def handler(request: httpx.Request) -> httpx.Response:
        cont = request.url.params.get("continuation")
        if cont is None:
            return httpx.Response(
                200,
                json={
                    "events": [{"id": "a"}],
                    "pagination": {"has_more_items": True, "continuation": "TOK"},
                },
            )
        return httpx.Response(
            200, json={"events": [{"id": "b"}], "pagination": {"has_more_items": False}}
        )

    items = await _client(handler).paginate("/events/", {}, "events")
    assert [i["id"] for i in items] == ["a", "b"]


# ── client: retry / backoff / rate-limit ────────────────────────────


async def test_client_retries_on_429_then_succeeds():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429, headers={"Retry-After": "0"}, json={})
        return httpx.Response(200, json={"ok": True})

    data = await _client(handler).get("/anything")
    assert data == {"ok": True}
    assert calls["n"] == 2  # retried once


async def test_client_raises_after_exhausting_retries():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={})

    with pytest.raises(httpx.HTTPStatusError):
        await _client(handler).get("/boom")


# ── provider: fetch + sync ──────────────────────────────────────────


def _provider_handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path.endswith("/users/me/organizations/"):
        return httpx.Response(
            200, json={"organizations": [{"id": "org1"}], "pagination": {"has_more_items": False}}
        )
    if "/organizations/org1/events/" in path:
        return httpx.Response(
            200, json={"events": [RAW_EVENT], "pagination": {"has_more_items": False}}
        )
    return httpx.Response(404, json={})


async def test_provider_fetch_resolves_orgs_then_events():
    provider = EventbriteProvider(client=_client(_provider_handler), scrape_enabled=False)
    raws = await provider.fetch(FetchContext(cities=["San Francisco"]))
    assert len(raws) == 1
    assert raws[0]["id"] == "123"


async def test_provider_sync_normalizes_and_validates():
    provider = EventbriteProvider(client=_client(_provider_handler), scrape_enabled=False)
    result = await provider.sync(FetchContext())
    assert result.fetched == 1
    assert len(result.events) == 1
    assert result.events[0].external_id == "123"
    assert not result.errors


async def test_provider_combines_api_and_scrape_and_prefers_api_duplicate():
    scraped_duplicate = (
        SERVER_DATA_HTML.replace('"id": "456"', '"id": "123"')
        .replace('"eventbrite_event_id": "456"', '"eventbrite_event_id": "123"')
        .replace("tickets-456", "tickets-123")
        .replace('data-event-id="456"', 'data-event-id="123"')
    )

    def scrape_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=scraped_duplicate)

    provider = EventbriteProvider(
        client=_client(_provider_handler), scrape_client=_scrape_client(scrape_handler)
    )
    result = await provider.sync(FetchContext(cities=["Bangalore"]))
    assert result.fetched == 1
    assert len(result.events) == 1
    assert result.events[0].title == "Tech Talk"


async def test_provider_scrapes_when_api_fails():
    def api_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "invalid token"})

    def scrape_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=SERVER_DATA_HTML)

    provider = EventbriteProvider(
        client=_client(api_handler), scrape_client=_scrape_client(scrape_handler)
    )
    result = await provider.sync(FetchContext(cities=["Bangalore"]))
    assert result.fetched == 1
    assert len(result.events) == 1
    assert result.events[0].external_id == "456"
    assert len(result.errors) == 1
    assert result.errors[0].startswith("Eventbrite API failed:")


async def test_provider_reports_unsupported_city_without_requesting():
    calls = {"n": 0}

    def scrape_handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, text=SERVER_DATA_HTML)

    provider = EventbriteProvider(
        scrape_client=_scrape_client(scrape_handler), api_enabled=False, scrape_enabled=True
    )
    result = await provider.sync(FetchContext(cities=["Unknown City"]))
    assert result.fetched == 0
    assert calls["n"] == 0
    assert result.errors == ["unsupported Eventbrite city: Unknown City"]
