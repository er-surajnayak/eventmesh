"""Map raw Eventbrite v3 event objects into the normalized model."""

from datetime import datetime

from app.modules.providers.base import NormalizedEvent


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def to_normalized(raw: dict) -> NormalizedEvent | None:
    """Return a NormalizedEvent, or None if the payload lacks essentials."""
    external_id = raw.get("id")
    start_time = _parse_dt((raw.get("start") or {}).get("utc"))
    title = (raw.get("name") or {}).get("text")
    url = raw.get("url")
    if not (external_id and start_time and title and url):
        return None

    venue = raw.get("venue") or {}
    address = venue.get("address") or {}
    logo = raw.get("logo") or {}

    return NormalizedEvent(
        provider="eventbrite",
        external_id=str(external_id),
        url=url,
        title=title,
        description=(raw.get("description") or {}).get("text"),
        image_url=logo.get("url"),
        start_time=start_time,
        end_time=_parse_dt((raw.get("end") or {}).get("utc")),
        timezone=(raw.get("start") or {}).get("timezone"),
        city=address.get("city"),
        venue=venue.get("name"),
        is_online=bool(raw.get("online_event")),
        is_free=bool(raw.get("is_free", False)),
        currency=raw.get("currency"),
        category=None,
    )
