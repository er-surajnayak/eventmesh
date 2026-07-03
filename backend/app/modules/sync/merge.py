"""Merge engine — deterministic canonical selection within dedup groups.

For each ``canonical_group_id`` of active imported events, exactly one row is
marked canonical. Selection is deterministic:
  1. provider priority (official APIs beat scrapers),
  2. metadata completeness (more filled fields wins),
  3. stable tiebreak on (provider, external_id).
Same inputs always yield the same canonical, so the visible feed is stable.
"""

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.modules.providers.dedup import provider_rank
from app.modules.sync.models import ImportedEvent, ImportedStatus

logger = get_logger(__name__)

# Fields that count toward "completeness" when breaking priority ties.
_COMPLETENESS_FIELDS = (
    "description",
    "image_url",
    "venue",
    "city",
    "end_time",
    "timezone",
    "price_cents",
)


def _completeness(event: ImportedEvent) -> int:
    return sum(1 for f in _COMPLETENESS_FIELDS if getattr(event, f) is not None)


def _canonical_sort_key(event: ImportedEvent) -> tuple:
    # Lower tuple sorts first -> that row becomes canonical.
    return (
        -provider_rank(event.provider),
        -_completeness(event),
        event.provider,
        event.external_id,
    )


def select_canonical(members: list[ImportedEvent]) -> ImportedEvent:
    return sorted(members, key=_canonical_sort_key)[0]


class MergeEngine:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def recompute_canonical(self) -> dict:
        """Recompute is_canonical across all active imported events."""
        result = await self._db.execute(
            select(ImportedEvent).where(ImportedEvent.status == ImportedStatus.active)
        )
        events = list(result.scalars().all())

        groups: dict = defaultdict(list)
        for event in events:
            groups[event.canonical_group_id].append(event)

        changed = 0
        for members in groups.values():
            winner = select_canonical(members)
            for event in members:
                should_be = event.id == winner.id
                if event.is_canonical != should_be:
                    event.is_canonical = should_be
                    changed += 1

        await self._db.commit()
        stats = {"groups": len(groups), "events": len(events), "canonical_updates": changed}
        logger.info("merge_recomputed", **stats)
        return stats
