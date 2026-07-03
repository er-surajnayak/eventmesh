"""Registration & capacity logic, kept separate from event CRUD and lifecycle."""

from datetime import UTC, datetime

from app.core.exceptions import ConflictError, NotFoundError
from app.modules.events.models import (
    EventRegistration,
    EventStatus,
    NativeEvent,
    RegistrationStatus,
)
from app.modules.events.registration_repository import RegistrationRepository


class RegistrationService:
    def __init__(self, repository: RegistrationRepository) -> None:
        self._repo = repository

    async def register(self, event: NativeEvent, user_id: str) -> EventRegistration:
        if event.status != EventStatus.published:
            raise ConflictError("Registration is only open for published events.")
        if not event.registration_required:
            raise ConflictError("This event does not use EventMesh registration.")
        if event.registration_closes_at and event.registration_closes_at < datetime.now(UTC):
            raise ConflictError("Registration has closed for this event.")

        existing = await self._repo.get(event.id, user_id)
        if existing and existing.status != RegistrationStatus.cancelled:
            return existing  # idempotent

        # Capacity → waitlist once confirmed registrations reach the limit.
        status = RegistrationStatus.registered
        if event.capacity is not None:
            if await self._repo.count_registered(event.id) >= event.capacity:
                status = RegistrationStatus.waitlisted

        if existing is not None:  # reactivate a previously cancelled registration
            existing.status = status
            await self._repo.commit()
            return existing

        registration = EventRegistration(native_event_id=event.id, user_id=user_id, status=status)
        await self._repo.add(registration)
        await self._repo.commit()
        return registration

    async def cancel(self, event: NativeEvent, user_id: str) -> EventRegistration:
        registration = await self._repo.get(event.id, user_id)
        if registration is None or registration.status == RegistrationStatus.cancelled:
            raise NotFoundError("No active registration found.")
        registration.status = RegistrationStatus.cancelled
        await self._repo.commit()
        return registration

    async def list_for_event(self, event: NativeEvent) -> list[EventRegistration]:
        return await self._repo.list_for_event(event.id)

    async def list_for_user(self, user_id: str) -> list[EventRegistration]:
        return await self._repo.list_for_user(user_id)
