"""Synchronization orchestrator.

Runs every enabled provider fail-soft: one provider erroring never aborts the
run or corrupts existing data. Produces a SyncReport and persists a SyncRun with
per-provider health metrics. Cross-provider canonical selection is intentionally
naive here (first-in-group wins) — 4E's merge engine refines it by priority.
"""

import asyncio
import time
import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.modules.providers.base import FetchContext, NormalizedEvent
from app.modules.providers.dedup import dedup_hash
from app.modules.providers.registry import enabled_providers
from app.modules.sync.merge import MergeEngine
from app.modules.sync.models import ImportedEvent, ImportedStatus, SyncRun, SyncStatus
from app.modules.sync.reports import ProviderHealth, SyncReport
from app.modules.sync.repository import ImportedEventRepository, SyncRunRepository

logger = get_logger(__name__)

_PROVIDER_TIMEOUT_SECONDS = 120


class SyncOrchestrator:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._runs = SyncRunRepository(db)
        self._imported = ImportedEventRepository(db)

    async def run(self, ctx: FetchContext) -> SyncReport:
        started = datetime.now(UTC)
        run = await self._runs.add(SyncRun(started_at=started, status=SyncStatus.running))
        await self._runs.commit()

        healths: list[ProviderHealth] = []
        for provider in enabled_providers():
            healths.append(await self._run_provider(provider, ctx))

        # Merge is fail-soft: a merge error never fails the whole run.
        merge_stats: dict = {}
        try:
            merge_stats = await MergeEngine(self._db).recompute_canonical()
        except Exception as exc:  # noqa: BLE001
            logger.warning("merge_failed", error=str(exc))
            merge_stats = {"error": str(exc)}

        status = self._overall_status(healths)
        totals = self._aggregate(healths)
        totals["merge"] = merge_stats
        run.finished_at = datetime.now(UTC)
        run.status = status
        run.totals = totals
        await self._runs.commit()

        logger.info("sync_completed", run_id=str(run.id), status=status, totals=totals)
        return SyncReport(
            run_id=str(run.id),
            status=status,
            started_at=started,
            finished_at=run.finished_at,
            providers=healths,
            totals=totals,
        )

    async def _run_provider(self, provider, ctx: FetchContext) -> ProviderHealth:
        slug = provider.meta.slug
        t0 = time.monotonic()
        try:
            result = await asyncio.wait_for(provider.sync(ctx), timeout=_PROVIDER_TIMEOUT_SECONDS)
            stored, duplicates = await self._store(slug, result.events)
            return ProviderHealth(
                provider=slug,
                ok=True,
                fetched=result.fetched,
                valid=len(result.events),
                stored=stored,
                duplicates=duplicates,
                errors=result.errors,
                duration_ms=int((time.monotonic() - t0) * 1000),
            )
        except Exception as exc:  # noqa: BLE001 - isolate a failing provider
            await self._imported.rollback()
            logger.warning("provider_sync_failed", provider=slug, error=str(exc))
            return ProviderHealth(
                provider=slug,
                ok=False,
                errors=[str(exc)],
                duration_ms=int((time.monotonic() - t0) * 1000),
            )

    async def _store(self, provider: str, events: list[NormalizedEvent]) -> tuple[int, int]:
        stored = 0
        duplicates = 0
        now = datetime.now(UTC)
        for event in events:
            digest = dedup_hash(event)
            existing = await self._imported.get(event.provider, event.external_id)
            if existing is not None:
                self._apply(existing, event, digest, now, is_new=False)
                stored += 1
                continue

            group_id = await self._imported.group_id_for_hash(digest)
            joins_existing_group = group_id is not None
            if joins_existing_group:
                duplicates += 1
            row = ImportedEvent(
                canonical_group_id=group_id or uuid.uuid4(),
                is_canonical=not joins_existing_group,
                first_seen_at=now,
            )
            self._apply(row, event, digest, now, is_new=True)
            self._imported.add(row)
            stored += 1
        await self._imported.commit()
        return stored, duplicates

    @staticmethod
    def _apply(
        row: ImportedEvent, event: NormalizedEvent, digest: str, now: datetime, *, is_new: bool
    ) -> None:
        row.provider = event.provider
        row.external_id = event.external_id
        row.url = event.url
        row.title = event.title
        row.description = event.description
        row.image_url = event.image_url
        row.start_time = event.start_time
        row.end_time = event.end_time
        row.timezone = event.timezone
        row.city = event.city
        row.venue = event.venue
        row.is_online = event.is_online
        row.is_free = event.is_free
        row.price_cents = event.price_cents
        row.currency = event.currency
        row.category = event.category
        row.dedup_hash = digest
        row.status = ImportedStatus.active
        row.last_seen_at = now

    @staticmethod
    def _overall_status(healths: list[ProviderHealth]) -> SyncStatus:
        if not healths:
            return SyncStatus.success
        ok = sum(1 for h in healths if h.ok)
        if ok == len(healths):
            return SyncStatus.success
        if ok == 0:
            return SyncStatus.failed
        return SyncStatus.partial

    @staticmethod
    def _aggregate(healths: list[ProviderHealth]) -> dict:
        return {
            "providers": len(healths),
            "ok": sum(1 for h in healths if h.ok),
            "fetched": sum(h.fetched for h in healths),
            "valid": sum(h.valid for h in healths),
            "stored": sum(h.stored for h in healths),
            "duplicates": sum(h.duplicates for h in healths),
        }
