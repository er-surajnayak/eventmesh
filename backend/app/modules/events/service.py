"""Native event business logic (3A: CRUD)."""

import uuid

from app.core.exceptions import NotFoundError
from app.modules.events.models import NativeEvent
from app.modules.events.repository import EventRepository
from app.modules.events.schemas import EventCreate, EventUpdate
from app.modules.organizers.models import Organization
from app.shared.slugs import unique_slug


class EventService:
    def __init__(self, repository: EventRepository) -> None:
        self._repo = repository

    async def create(self, org: Organization, data: EventCreate) -> NativeEvent:
        # Public slug generated once from the title; stable across later edits.
        slug = await unique_slug(data.title, self._repo.slug_exists)
        event = NativeEvent(organization_id=org.id, slug=slug, **data.model_dump())
        await self._repo.add(event)
        await self._repo.commit()
        return event

    async def get_for_org(self, org: Organization, event_id: uuid.UUID) -> NativeEvent:
        event = await self._repo.get(event_id)
        if event is None or event.organization_id != org.id:
            raise NotFoundError("Event not found.")
        return event

    async def list_for_org(self, org: Organization) -> list[NativeEvent]:
        return await self._repo.list_for_org(org.id)

    async def update(self, event: NativeEvent, data: EventUpdate) -> NativeEvent:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(event, field, value)
        await self._repo.commit()
        return event

    async def delete(self, event: NativeEvent) -> None:
        await self._repo.delete(event)
        await self._repo.commit()
