"""Data access for event registrations."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.events.models import EventRegistration, RegistrationStatus


class RegistrationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get(self, event_id: uuid.UUID, user_id: str) -> EventRegistration | None:
        result = await self._db.execute(
            select(EventRegistration).where(
                EventRegistration.native_event_id == event_id,
                EventRegistration.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def count_active(self, event_id: uuid.UUID) -> int:
        """Count non-cancelled registrations (registered + waitlisted)."""
        result = await self._db.execute(
            select(func.count())
            .select_from(EventRegistration)
            .where(
                EventRegistration.native_event_id == event_id,
                EventRegistration.status != RegistrationStatus.cancelled,
            )
        )
        return result.scalar() or 0

    async def count_registered(self, event_id: uuid.UUID) -> int:
        """Count confirmed (non-waitlisted, non-cancelled) registrations."""
        result = await self._db.execute(
            select(func.count())
            .select_from(EventRegistration)
            .where(
                EventRegistration.native_event_id == event_id,
                EventRegistration.status == RegistrationStatus.registered,
            )
        )
        return result.scalar() or 0

    async def list_for_event(self, event_id: uuid.UUID) -> list[EventRegistration]:
        result = await self._db.execute(
            select(EventRegistration)
            .where(EventRegistration.native_event_id == event_id)
            .order_by(EventRegistration.created_at.asc())
        )
        return list(result.scalars().all())

    async def list_for_user(self, user_id: str) -> list[EventRegistration]:
        result = await self._db.execute(
            select(EventRegistration)
            .where(EventRegistration.user_id == user_id)
            .order_by(EventRegistration.created_at.desc())
        )
        return list(result.scalars().all())

    async def add(self, registration: EventRegistration) -> EventRegistration:
        self._db.add(registration)
        await self._db.flush()
        return registration

    async def commit(self) -> None:
        await self._db.commit()

    async def rollback(self) -> None:
        await self._db.rollback()
