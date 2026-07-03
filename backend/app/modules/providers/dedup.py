"""Deduplication infrastructure.

Cross-provider duplicates (the same event on Eventbrite + Meetup + Luma) share a
``dedup_hash`` derived from normalized title + hour-bucketed start + city. The
canonical winner within a group is chosen by provider priority (official APIs
beat scrapers). Heuristic by design — made observable, not assumed perfect.
"""

import hashlib
import re

from app.modules.providers.base import NormalizedEvent

_NON_ALNUM = re.compile(r"[^a-z0-9]+")

# Higher rank wins the canonical slot within a dedup group.
PROVIDER_PRIORITY: dict[str, int] = {
    "eventbrite": 3,
    "ticketmaster": 3,
    "meetup": 2,
    "luma": 1,
}


def _normalize_title(title: str) -> str:
    return _NON_ALNUM.sub(" ", title.lower()).strip()


def dedup_hash(event: NormalizedEvent) -> str:
    """Stable hash grouping likely-duplicate events across providers."""
    title = _normalize_title(event.title)
    bucket = event.start_time.replace(minute=0, second=0, microsecond=0).isoformat()
    city = (event.city or "").lower().strip()
    return hashlib.sha1(f"{title}|{bucket}|{city}".encode()).hexdigest()


def provider_rank(provider: str) -> int:
    return PROVIDER_PRIORITY.get(provider.lower(), 0)
