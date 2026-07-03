"""Parse Luma HTML into a uniform raw-event dict.

Structured data first, HTML selectors last:
  1. schema.org JSON-LD (Event / ItemList)
  2. Next.js ``__NEXT_DATA__`` (structured JSON Luma server-renders)
  3. Open Graph meta tags (single-event pages)
HTML selectors would be the final fallback (not needed while the above exist).

All three emit the same uniform dict so the mapper stays single-shape.
"""

import json

from bs4 import BeautifulSoup


def _first(value: object) -> object:
    if isinstance(value, list):
        return value[0] if value else None
    return value


def _luma_id(url: str | None) -> str | None:
    if not url:
        return None
    return url.rstrip("/").split("/")[-1]


def _price_from_offers(offers: object) -> tuple[int | None, str | None]:
    offer = _first(offers)
    if isinstance(offer, dict):
        try:
            price = float(offer.get("price"))
            if price > 0:
                return round(price * 100), offer.get("priceCurrency")
        except (TypeError, ValueError):
            pass
    return None, None


def _schema_events(data: object) -> list[dict]:
    items: list = []
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        node_type = data.get("@type")
        if node_type == "ItemList":
            items = [el.get("item", el) for el in data.get("itemListElement", [])]
        elif node_type == "Event":
            items = [data]
        elif "@graph" in data:
            items = data["@graph"]
    return [i for i in items if isinstance(i, dict) and i.get("@type") == "Event"]


def _uniform_from_schema(ev: dict) -> dict:
    location = ev.get("location") if isinstance(ev.get("location"), dict) else {}
    address = location.get("address") if isinstance(location.get("address"), dict) else {}
    price_cents, currency = _price_from_offers(ev.get("offers"))
    return {
        "external_id": _luma_id(ev.get("url")),
        "url": ev.get("url"),
        "title": ev.get("name"),
        "description": ev.get("description"),
        "image_url": _first(ev.get("image")),
        "start": ev.get("startDate"),
        "end": ev.get("endDate"),
        "timezone": None,
        "city": address.get("addressLocality"),
        "venue": location.get("name"),
        "is_online": "Online" in (ev.get("eventAttendanceMode") or ""),
        "price_cents": price_cents,
        "currency": currency,
    }


def _uniform_from_luma(o: dict) -> dict:
    slug = o.get("url")
    url = slug if str(slug).startswith("http") else (f"https://lu.ma/{slug}" if slug else None)
    geo = o.get("geo_address_info") if isinstance(o.get("geo_address_info"), dict) else {}
    return {
        "external_id": o.get("api_id") or slug,
        "url": url,
        "title": o.get("name"),
        "description": o.get("description_short") or o.get("description"),
        "image_url": o.get("cover_url"),
        "start": o.get("start_at"),
        "end": o.get("end_at"),
        "timezone": o.get("timezone"),
        "city": geo.get("city"),
        "venue": geo.get("address"),
        "is_online": o.get("location_type") == "online" or bool(o.get("is_online")),
        "price_cents": None,
        "currency": None,
    }


def _from_json_ld(soup: BeautifulSoup) -> list[dict]:
    out: list[dict] = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        out.extend(_uniform_from_schema(ev) for ev in _schema_events(data))
    return out


def _from_next_data(soup: BeautifulSoup) -> list[dict]:
    tag = soup.find("script", id="__NEXT_DATA__")
    if tag is None:
        return []
    try:
        data = json.loads(tag.string or "")
    except (json.JSONDecodeError, TypeError):
        return []

    found: list[dict] = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            if (
                node.get("name")
                and node.get("start_at")
                and (node.get("url") or node.get("api_id"))
            ):
                found.append(_uniform_from_luma(node))
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)
    seen: set[str] = set()
    unique: list[dict] = []
    for event in found:
        url = event.get("url")
        if url and url not in seen:
            seen.add(url)
            unique.append(event)
    return unique


def _from_open_graph(soup: BeautifulSoup) -> dict | None:
    def og(prop: str) -> str | None:
        tag = soup.find("meta", attrs={"property": prop}) or soup.find("meta", attrs={"name": prop})
        return tag.get("content") if tag else None

    title, url, start = og("og:title"), og("og:url"), og("event:start_time")
    if not (title and url and start):
        return None
    return {
        "external_id": _luma_id(url),
        "url": url,
        "title": title,
        "description": og("og:description"),
        "image_url": og("og:image"),
        "start": start,
        "end": og("event:end_time"),
        "timezone": None,
        "city": None,
        "venue": None,
        "is_online": False,
        "price_cents": None,
        "currency": None,
    }


def parse_events(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    events = _from_json_ld(soup)
    if events:
        return events
    events = _from_next_data(soup)
    if events:
        return events
    og_event = _from_open_graph(soup)
    return [og_event] if og_event else []
