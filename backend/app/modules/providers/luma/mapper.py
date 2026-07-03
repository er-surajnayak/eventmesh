"""Map Luma's uniform raw dict into the normalized model."""

from datetime import datetime

from app.modules.providers.base import NormalizedEvent


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def to_normalized(raw: dict, city: str | None = None) -> NormalizedEvent | None:
    url = raw.get("url")
    title = raw.get("title")
    start_time = _parse_dt(raw.get("start"))
    if not (url and title and start_time):
        return None

    price_cents = raw.get("price_cents")
    return NormalizedEvent(
        provider="luma",
        external_id=str(raw.get("external_id") or url),
        url=url,
        title=title,
        description=raw.get("description"),
        image_url=raw.get("image_url"),
        start_time=start_time,
        end_time=_parse_dt(raw.get("end")),
        timezone=raw.get("timezone"),
        city=raw.get("city") or city,
        venue=raw.get("venue"),
        is_online=bool(raw.get("is_online")),
        is_free=price_cents in (None, 0),
        price_cents=price_cents,
        currency=raw.get("currency"),
    )
