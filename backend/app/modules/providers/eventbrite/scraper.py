"""Extract public Eventbrite city-listing events without a browser.

Extraction order:
1. ``window.__SERVER_DATA__`` destination events (precise time and timezone).
2. schema.org JSON-LD ItemList/Event nodes (stable degraded fallback).

Both sources are converted to the official API event shape so the existing
Eventbrite mapper remains the only normalization path.
"""

import json
import re
from datetime import UTC, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from bs4 import BeautifulSoup

_SERVER_DATA_MARKER = "window.__SERVER_DATA__"
_EVENT_ID = re.compile(r"(?:tickets-|/events/)(\d+)(?:[/?]|$)")


def _first(value: object) -> object:
    if isinstance(value, list):
        return value[0] if value else None
    return value


def _dict(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def _event_id(event: dict) -> str | None:
    value = event.get("id") or event.get("eventbrite_event_id") or event.get("eid")
    if value:
        return str(value)
    url = str(event.get("url") or "")
    match = _EVENT_ID.search(url)
    return match.group(1) if match else None


def _utc_datetime(date: object, time: object, timezone: object) -> str | None:
    if not date:
        return None
    value = f"{date}T{time or '00:00'}"
    try:
        local = datetime.fromisoformat(value)
        if timezone:
            local = local.replace(tzinfo=ZoneInfo(str(timezone))).astimezone(UTC)
        return local.isoformat().replace("+00:00", "Z")
    except (TypeError, ValueError, ZoneInfoNotFoundError):
        return None


def _category(tags: object) -> dict | None:
    if not isinstance(tags, list):
        return None
    for tag in tags:
        if not isinstance(tag, dict) or tag.get("prefix") != "EventbriteCategory":
            continue
        localized = _dict(tag.get("localized"))
        name = localized.get("display_name") or tag.get("display_name")
        if name:
            return {"short_name": name}
    return None


def _paid_status_by_id(soup: BeautifulSoup) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for anchor in soup.select("a[data-event-id][data-event-paid-status]"):
        event_id = anchor.get("data-event-id")
        status = anchor.get("data-event-paid-status")
        if event_id and status:
            statuses[str(event_id)] = str(status).lower()
    return statuses


def _api_shape_from_destination(event: dict, paid_status: str | None) -> dict | None:
    external_id = _event_id(event)
    title = event.get("name")
    url = event.get("url")
    start = _utc_datetime(event.get("start_date"), event.get("start_time"), event.get("timezone"))
    if not (external_id and title and url and start):
        return None

    venue = _dict(event.get("primary_venue"))
    address = _dict(venue.get("address"))
    image = _dict(event.get("image"))
    end = _utc_datetime(event.get("end_date"), event.get("end_time"), event.get("timezone"))

    return {
        "id": external_id,
        "name": {"text": title},
        "description": {"text": event.get("summary") or event.get("full_description")},
        "url": str(url).split("?", 1)[0],
        "start": {"utc": start, "timezone": event.get("timezone")},
        "end": {"utc": end} if end else {},
        "is_free": paid_status == "free",
        "online_event": bool(event.get("is_online_event")),
        "currency": None,
        "logo": {"url": image.get("url")},
        "venue": {
            "name": venue.get("name"),
            "address": {"city": address.get("city")},
        },
        "category": _category(event.get("tags")),
    }


def _load_server_data(soup: BeautifulSoup) -> dict | None:
    for script in soup.find_all("script"):
        text = script.string or script.get_text() or ""
        marker = text.find(_SERVER_DATA_MARKER)
        if marker < 0:
            continue
        start = text.find("{", marker + len(_SERVER_DATA_MARKER))
        if start < 0:
            continue
        try:
            data, _ = json.JSONDecoder().raw_decode(text[start:])
        except (json.JSONDecodeError, TypeError):
            continue
        return data if isinstance(data, dict) else None
    return None


def _destination_events(data: object) -> list[dict]:
    found: list[dict] = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            if node.get("_type") == "destination_event":
                found.append(node)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(data)
    return found


def _schema_events(data: object) -> list[dict]:
    items: list = []
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        if data.get("@type") == "ItemList":
            items = [item.get("item", item) for item in data.get("itemListElement", [])]
        elif data.get("@type") == "Event":
            items = [data]
        elif isinstance(data.get("@graph"), list):
            items = data["@graph"]
    return [item for item in items if isinstance(item, dict) and item.get("@type") == "Event"]


def _offer_is_free(offers: object) -> bool:
    offer = _first(offers)
    if not isinstance(offer, dict):
        return False
    try:
        return float(str(offer.get("price"))) == 0
    except (TypeError, ValueError):
        return False


def _api_shape_from_schema(event: dict, fallback_city: str | None) -> dict | None:
    external_id = _event_id(event)
    title = event.get("name")
    url = event.get("url")
    start = event.get("startDate")
    if not (external_id and title and url and start):
        return None

    location = _dict(event.get("location"))
    address = _dict(location.get("address"))
    image = _first(event.get("image"))
    attendance = str(event.get("eventAttendanceMode") or "")
    offer = _first(event.get("offers"))
    currency = offer.get("priceCurrency") if isinstance(offer, dict) else None

    return {
        "id": external_id,
        "name": {"text": title},
        "description": {"text": event.get("description")},
        "url": str(url).split("?", 1)[0],
        "start": {"utc": start, "timezone": None},
        "end": {"utc": event.get("endDate")} if event.get("endDate") else {},
        "is_free": _offer_is_free(event.get("offers")),
        "online_event": "Online" in attendance,
        "currency": currency,
        "logo": {"url": image if isinstance(image, str) else None},
        "venue": {
            "name": location.get("name"),
            "address": {"city": address.get("addressLocality") or fallback_city},
        },
        "category": None,
    }


def _from_server_data(soup: BeautifulSoup) -> list[dict]:
    data = _load_server_data(soup)
    if data is None:
        return []
    paid_statuses = _paid_status_by_id(soup)
    events: list[dict] = []
    seen: set[str] = set()
    for destination in _destination_events(data):
        event_id = _event_id(destination)
        if not event_id or event_id in seen:
            continue
        raw = _api_shape_from_destination(destination, paid_statuses.get(event_id))
        if raw is not None:
            seen.add(event_id)
            events.append(raw)
    return events


def _from_json_ld(soup: BeautifulSoup, fallback_city: str | None) -> list[dict]:
    events: list[dict] = []
    seen: set[str] = set()
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        for schema_event in _schema_events(data):
            event_id = _event_id(schema_event)
            if not event_id or event_id in seen:
                continue
            raw = _api_shape_from_schema(schema_event, fallback_city)
            if raw is not None:
                seen.add(event_id)
                events.append(raw)
    return events


def parse_events(html: str, fallback_city: str | None = None) -> list[dict]:
    """Return unique API-shaped events from one public city listing page."""
    soup = BeautifulSoup(html, "html.parser")
    events = _from_server_data(soup)
    return events if events else _from_json_ld(soup, fallback_city)
