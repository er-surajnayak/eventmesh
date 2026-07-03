"""Data access for native events."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.events.models import EventStatus, EventVisibility, NativeEvent


class EventRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add(self, event: NativeEvent) -> NativeEvent:
        self._db.add(event)
        await self._db.flush()
        return event

    async def get(self, event_id: uuid.UUID) -> NativeEvent | None:
        result = await self._db.execute(select(NativeEvent).where(NativeEvent.id == event_id))
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> NativeEvent | None:
        result = await self._db.execute(select(NativeEvent).where(NativeEvent.slug == slug))
        return result.scalar_one_or_none()

    async def slug_exists(self, slug: str) -> bool:
        result = await self._db.execute(
            select(func.count()).select_from(NativeEvent).where(NativeEvent.slug == slug)
        )
        return (result.scalar() or 0) > 0

    async def list_for_org(self, organization_id: uuid.UUID) -> list[NativeEvent]:
        result = await self._db.execute(
            select(NativeEvent)
            .where(NativeEvent.organization_id == organization_id)
            .order_by(NativeEvent.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_public(self, *, limit: int, offset: int) -> tuple[int, list[NativeEvent]]:
        """Published + public events, newest-first, paginated."""
        base = select(NativeEvent).where(
            NativeEvent.status == EventStatus.published,
            NativeEvent.visibility == EventVisibility.public,
        )
        total = (
            await self._db.execute(select(func.count()).select_from(base.subquery()))
        ).scalar() or 0
        result = await self._db.execute(
            base.order_by(NativeEvent.start_time.asc().nulls_last()).limit(limit).offset(offset)
        )
        return total, list(result.scalars().all())

    async def delete(self, event: NativeEvent) -> None:
        await self._db.delete(event)

    async def commit(self) -> None:
        await self._db.commit()

    async def rollback(self) -> None:
        await self._db.rollback()
