"""Eventbrite connector tests — all responses mocked (no live API)."""

import httpx
import pytest

from app.modules.providers.base import FetchContext
from app.modules.providers.eventbrite.client import EventbriteClient
from app.modules.providers.eventbrite.mapper import to_normalized
from app.modules.providers.eventbrite.provider import EventbriteProvider

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


def _client(handler) -> EventbriteClient:
    http = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url=BASE)
    return EventbriteClient("token", BASE, client=http, backoff_base=0.001)


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


def test_mapper_returns_none_when_missing_essentials():
    assert to_normalized({"id": "1", "name": {"text": "No date"}}) is None


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
    provider = EventbriteProvider(client=_client(_provider_handler))
    raws = await provider.fetch(FetchContext(cities=["San Francisco"]))
    assert len(raws) == 1
    assert raws[0]["id"] == "123"


async def test_provider_sync_normalizes_and_validates():
    provider = EventbriteProvider(client=_client(_provider_handler))
    result = await provider.sync(FetchContext())
    assert result.fetched == 1
    assert len(result.events) == 1
    assert result.events[0].external_id == "123"
    assert not result.errors
