"""Data access for imported events and sync runs."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.sync.models import ImportedEvent, SyncRun


class SyncRunRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add(self, run: SyncRun) -> SyncRun:
        self._db.add(run)
        await self._db.flush()
        return run

    async def list_recent(self, limit: int = 20) -> list[SyncRun]:
        result = await self._db.execute(
            select(SyncRun).order_by(SyncRun.started_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def commit(self) -> None:
        await self._db.commit()


class ImportedEventRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get(self, provider: str, external_id: str) -> ImportedEvent | None:
        result = await self._db.execute(
            select(ImportedEvent).where(
                ImportedEvent.provider == provider,
                ImportedEvent.external_id == external_id,
            )
        )
        return result.scalar_one_or_none()

    async def group_id_for_hash(self, dedup_hash: str) -> uuid.UUID | None:
        """Return an existing canonical_group_id for this dedup hash, if any."""
        result = await self._db.execute(
            select(ImportedEvent.canonical_group_id)
            .where(ImportedEvent.dedup_hash == dedup_hash)
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def group_members(self, group_id: uuid.UUID) -> list[ImportedEvent]:
        result = await self._db.execute(
            select(ImportedEvent).where(ImportedEvent.canonical_group_id == group_id)
        )
        return list(result.scalars().all())

    def add(self, event: ImportedEvent) -> None:
        self._db.add(event)

    async def flush(self) -> None:
        await self._db.flush()

    async def commit(self) -> None:
        await self._db.commit()

    async def rollback(self) -> None:
        await self._db.rollback()
