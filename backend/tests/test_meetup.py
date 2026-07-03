"""Meetup connector tests — mocked HTML fixtures (no live scraping)."""

import httpx
import pytest

from app.modules.providers.base import FetchContext
from app.modules.providers.meetup.client import MeetupClient
from app.modules.providers.meetup.mapper import to_normalized
from app.modules.providers.meetup.provider import MeetupProvider
from app.modules.providers.meetup.scraper import parse_events

# A realistic Meetup 'find' page fragment: schema.org JSON-LD ItemList of Events.
FIXTURE_HTML = """
<html><head>
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"ItemList","itemListElement":[
  {"@type":"ListItem","item":{
    "@type":"Event","name":"Rust Berlin Meetup",
    "url":"https://www.meetup.com/rust-berlin/events/123456/",
    "startDate":"2027-04-01T18:00:00+02:00","endDate":"2027-04-01T20:00:00+02:00",
    "location":{"@type":"Place","name":"Factory","address":{"@type":"PostalAddress","addressLocality":"Berlin"}},
    "image":"https://img/rust.jpg","description":"Async Rust",
    "eventAttendanceMode":"https://schema.org/OfflineEventAttendanceMode"}},
  {"@type":"ListItem","item":{
    "@type":"Event","name":"Online AI Night",
    "url":"https://www.meetup.com/ai/events/789/","startDate":"2027-04-05T17:00:00Z",
    "eventAttendanceMode":"https://schema.org/OnlineEventAttendanceMode",
    "offers":{"@type":"Offer","price":"15.00","priceCurrency":"USD"}}}
]}
</script></head><body>ignored</body></html>
"""


def _client(handler) -> MeetupClient:
    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return MeetupClient(client=http, min_delay=0, backoff_base=0.001)


# ── scraper ─────────────────────────────────────────────────────────


def test_scraper_extracts_events_from_json_ld():
    events = parse_events(FIXTURE_HTML)
    assert len(events) == 2
    assert events[0]["name"] == "Rust Berlin Meetup"


def test_scraper_handles_empty_or_bad_html():
    assert parse_events("<html><body>nothing</body></html>") == []
    assert parse_events('<script type="application/ld+json">not json</script>') == []


# ── mapper ──────────────────────────────────────────────────────────


def test_mapper_free_offline_event():
    raw = parse_events(FIXTURE_HTML)[0]
    ev = to_normalized(raw, city="Berlin")
    assert ev is not None
    assert ev.provider == "meetup"
    assert ev.external_id == "123456"  # extracted from /events/<id>/
    assert ev.city == "Berlin"
    assert ev.venue == "Factory"
    assert ev.is_online is False
    assert ev.is_free is True


def test_mapper_paid_online_event():
    raw = parse_events(FIXTURE_HTML)[1]
    ev = to_normalized(raw, city="Berlin")
    assert ev.is_online is True
    assert ev.is_free is False
    assert ev.price_cents == 1500
    assert ev.currency == "USD"


def test_mapper_returns_none_when_incomplete():
    assert to_normalized({"name": "No url or date"}) is None


# ── client: retry ───────────────────────────────────────────────────


async def test_client_retries_on_5xx_then_succeeds():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(503, text="busy")
        return httpx.Response(200, text="<html>ok</html>")

    html = await _client(handler).get_html("https://www.meetup.com/find/")
    assert "ok" in html
    assert calls["n"] == 2


async def test_client_raises_after_exhausting_retries():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="down")

    with pytest.raises(httpx.HTTPStatusError):
        await _client(handler).get_html("https://www.meetup.com/find/")


# ── provider: fetch + sync ──────────────────────────────────────────


def _fixture_handler(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, text=FIXTURE_HTML)


async def test_provider_fetch_tags_city():
    provider = MeetupProvider(client=_client(_fixture_handler))
    raws = await provider.fetch(FetchContext(cities=["Berlin"]))
    assert len(raws) == 2
    assert all(r["_city"] == "Berlin" for r in raws)


async def test_provider_sync_normalizes_and_validates():
    provider = MeetupProvider(client=_client(_fixture_handler))
    result = await provider.sync(FetchContext(cities=["Berlin"]))
    assert result.fetched == 2
    assert len(result.events) == 2
    assert {e.provider for e in result.events} == {"meetup"}
    assert not result.errors
