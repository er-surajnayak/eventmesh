"""Data access for native events."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.events.models import NativeEvent


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

    async def list_for_org(self, organization_id: uuid.UUID) -> list[NativeEvent]:
        result = await self._db.execute(
            select(NativeEvent)
            .where(NativeEvent.organization_id == organization_id)
            .order_by(NativeEvent.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete(self, event: NativeEvent) -> None:
        await self._db.delete(event)

    async def commit(self) -> None:
        await self._db.commit()

    async def rollback(self) -> None:
        await self._db.rollback()
