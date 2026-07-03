"""Map raw Meetup schema.org Event dicts into the normalized model."""

import re
from datetime import datetime

from app.modules.providers.base import NormalizedEvent

_EVENT_ID = re.compile(r"/events/(\d+)")


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _first(value: object) -> object:
    if isinstance(value, list):
        return value[0] if value else None
    return value


def to_normalized(raw: dict, city: str | None = None) -> NormalizedEvent | None:
    url = raw.get("url")
    title = raw.get("name")
    start_time = _parse_dt(raw.get("startDate"))
    if not (url and title and start_time):
        return None

    match = _EVENT_ID.search(url)
    external_id = match.group(1) if match else url

    location = raw.get("location") if isinstance(raw.get("location"), dict) else {}
    address = location.get("address") if isinstance(location.get("address"), dict) else {}
    attendance = raw.get("eventAttendanceMode") or ""

    is_free, price_cents, currency = True, None, None
    offer = _first(raw.get("offers"))
    if isinstance(offer, dict):
        try:
            price = float(offer.get("price"))
            if price > 0:
                is_free, price_cents, currency = (
                    False,
                    round(price * 100),
                    offer.get("priceCurrency"),
                )
        except (TypeError, ValueError):
            pass

    return NormalizedEvent(
        provider="meetup",
        external_id=str(external_id),
        url=url,
        title=title,
        description=raw.get("description"),
        image_url=_first(raw.get("image")),
        start_time=start_time,
        end_time=_parse_dt(raw.get("endDate")),
        city=address.get("addressLocality") or city,
        venue=location.get("name"),
        is_online="Online" in attendance,
        is_free=is_free,
        price_cents=price_cents,
        currency=currency,
    )
