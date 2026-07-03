"""Event lifecycle as explicit business actions.

Status only ever changes through these guarded transitions — never an arbitrary
status update from CRUD. Auto-approval (MVP) keeps the pending_review state in
the model but immediately advances to published.
"""

from datetime import UTC, datetime

from app.core.config import settings
from app.core.exceptions import ConflictError
from app.modules.events.models import EventStatus, NativeEvent
from app.modules.events.repository import EventRepository

# Allowed source -> target transitions.
ALLOWED_TRANSITIONS: dict[EventStatus, set[EventStatus]] = {
    EventStatus.draft: {
        EventStatus.preview,
        EventStatus.pending_review,
        EventStatus.cancelled,
        EventStatus.archived,
    },
    EventStatus.preview: {
        EventStatus.draft,
        EventStatus.pending_review,
        EventStatus.cancelled,
        EventStatus.archived,
    },
    EventStatus.pending_review: {
        EventStatus.published,
        EventStatus.draft,
        EventStatus.cancelled,
        EventStatus.archived,
    },
    EventStatus.published: {EventStatus.hidden, EventStatus.cancelled, EventStatus.archived},
    EventStatus.hidden: {EventStatus.published, EventStatus.cancelled, EventStatus.archived},
    EventStatus.cancelled: {EventStatus.archived},
    EventStatus.archived: set(),
}


class EventLifecycleService:
    def __init__(self, repository: EventRepository) -> None:
        self._repo = repository

    async def _transition(self, event: NativeEvent, target: EventStatus) -> NativeEvent:
        if target not in ALLOWED_TRANSITIONS[event.status]:
            raise ConflictError(f"Cannot move event from '{event.status}' to '{target}'.")
        event.status = target
        if target == EventStatus.published and event.published_at is None:
            event.published_at = datetime.now(UTC)
        await self._repo.commit()
        return event

    @staticmethod
    def _require_publishable(event: NativeEvent) -> None:
        if event.start_time is None:
            raise ConflictError("Set a start time before submitting or publishing.")

    async def to_preview(self, event: NativeEvent) -> NativeEvent:
        return await self._transition(event, EventStatus.preview)

    async def submit_for_review(self, event: NativeEvent) -> NativeEvent:
        """Organizer action to go live. Auto-approves in the MVP."""
        self._require_publishable(event)
        await self._transition(event, EventStatus.pending_review)
        if settings.auto_approve_events:
            return await self._transition(event, EventStatus.published)
        return event

    async def publish(self, event: NativeEvent) -> NativeEvent:
        """Approve a pending_review event (manual/moderator path)."""
        self._require_publishable(event)
        return await self._transition(event, EventStatus.published)

    async def hide(self, event: NativeEvent) -> NativeEvent:
        return await self._transition(event, EventStatus.hidden)

    async def unhide(self, event: NativeEvent) -> NativeEvent:
        return await self._transition(event, EventStatus.published)

    async def cancel(self, event: NativeEvent) -> NativeEvent:
        return await self._transition(event, EventStatus.cancelled)

    async def archive(self, event: NativeEvent) -> NativeEvent:
        return await self._transition(event, EventStatus.archived)
