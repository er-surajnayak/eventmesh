"""Luma connector tests — mocked HTML fixtures (no live scraping)."""

import json

import httpx

from app.modules.providers.base import FetchContext
from app.modules.providers.luma.mapper import to_normalized
from app.modules.providers.luma.provider import LumaProvider
from app.modules.providers.luma.scraper import parse_events
from app.modules.providers.scrape_client import ScrapeClient

# 1) schema.org JSON-LD (preferred structured source)
JSON_LD_HTML = """
<html><head>
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"ItemList","itemListElement":[
  {"@type":"ListItem","item":{
    "@type":"Event","name":"Founders Dinner","url":"https://lu.ma/abc123",
    "startDate":"2027-05-01T18:00:00Z","endDate":"2027-05-01T21:00:00Z",
    "location":{"@type":"Place","name":"Rooftop","address":{"addressLocality":"San Francisco"}},
    "image":"https://img/d.jpg","description":"Dinner",
    "eventAttendanceMode":"https://schema.org/OfflineEventAttendanceMode",
    "offers":{"@type":"Offer","price":"25","priceCurrency":"USD"}}}
]}
</script></head><body></body></html>
"""

# 2) Next.js __NEXT_DATA__ (structured JSON fallback)
_NEXT_JSON = json.dumps(
    {
        "props": {
            "pageProps": {
                "events": [
                    {
                        "api_id": "evt-1",
                        "name": "AI Hack Night",
                        "url": "ai-hack",
                        "start_at": "2027-06-01T17:00:00Z",
                        "cover_url": "https://img/ai.jpg",
                        "location_type": "online",
                        "geo_address_info": {"city": "Berlin"},
                    }
                ]
            }
        }
    }
)
NEXT_DATA_HTML = (
    '<html><head><script id="__NEXT_DATA__" type="application/json">'
    + _NEXT_JSON
    + "</script></head><body></body></html>"
)

# 3) Open Graph single-event page (structured, before HTML selectors)
OG_HTML = """
<html><head>
<meta property="og:title" content="Design Meetup" />
<meta property="og:url" content="https://lu.ma/design-xyz" />
<meta property="og:image" content="https://img/design.jpg" />
<meta property="event:start_time" content="2027-07-01T19:00:00Z" />
</head><body></body></html>
"""


def _client(handler) -> ScrapeClient:
    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return ScrapeClient(client=http, min_delay=0, backoff_base=0.001, source="luma")


# ── scraper: prefers structured data in order ───────────────────────


def test_scraper_json_ld_first():
    events = parse_events(JSON_LD_HTML)
    assert len(events) == 1
    assert events[0]["title"] == "Founders Dinner"
    assert events[0]["external_id"] == "abc123"
    assert events[0]["price_cents"] == 2500


def test_scraper_next_data_fallback():
    events = parse_events(NEXT_DATA_HTML)
    assert len(events) == 1
    assert events[0]["title"] == "AI Hack Night"
    assert events[0]["url"] == "https://lu.ma/ai-hack"
    assert events[0]["is_online"] is True
    assert events[0]["city"] == "Berlin"


def test_scraper_open_graph_last_resort():
    events = parse_events(OG_HTML)
    assert len(events) == 1
    assert events[0]["title"] == "Design Meetup"
    assert events[0]["start"] == "2027-07-01T19:00:00Z"


def test_scraper_empty_html():
    assert parse_events("<html><body>nothing</body></html>") == []


# ── mapper ──────────────────────────────────────────────────────────


def test_mapper_from_json_ld():
    ev = to_normalized(parse_events(JSON_LD_HTML)[0])
    assert ev is not None
    assert ev.provider == "luma"
    assert ev.city == "San Francisco"
    assert ev.is_free is False
    assert ev.price_cents == 2500


def test_mapper_from_next_data_online():
    ev = to_normalized(parse_events(NEXT_DATA_HTML)[0])
    assert ev.is_online is True
    assert ev.is_free is True
    assert ev.external_id == "evt-1"


def test_mapper_none_when_incomplete():
    assert to_normalized({"title": "no url/date"}) is None


# ── provider: fetch + sync ──────────────────────────────────────────


def _handler(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, text=JSON_LD_HTML)


async def test_provider_fetch_and_sync():
    provider = LumaProvider(client=_client(_handler))
    raws = await provider.fetch(FetchContext(cities=["San Francisco"]))
    assert len(raws) == 1 and raws[0]["_city"] == "San Francisco"

    result = await provider.sync(FetchContext(cities=["San Francisco"]))
    assert result.fetched == 1
    assert len(result.events) == 1
    assert result.events[0].provider == "luma"
    assert not result.errors
