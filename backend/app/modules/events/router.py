"""Native event routes (3A: CRUD), nested under an organization.

Authorization: all routes require the caller to be a member of the org (via the
OrgMember dependency). Events are created as drafts; lifecycle transitions and
public browsing arrive in 3B.
"""

import uuid

from fastapi import APIRouter, status

from app.api.v1.deps import DbSession
from app.modules.events.lifecycle import EventLifecycleService
from app.modules.events.repository import EventRepository
from app.modules.events.schemas import EventCreate, EventRead, EventUpdate
from app.modules.events.service import EventService
from app.modules.organizers.dependencies import OrgMember

router = APIRouter(prefix="/organizations/{slug}/events", tags=["events"])


def _service(db: DbSession) -> EventService:
    return EventService(EventRepository(db))


def _lifecycle(db: DbSession) -> EventLifecycleService:
    return EventLifecycleService(EventRepository(db))


@router.post("", response_model=EventRead, status_code=status.HTTP_201_CREATED)
async def create_event(payload: EventCreate, ctx: OrgMember, db: DbSession) -> EventRead:
    event = await _service(db).create(ctx.organization, payload)
    return EventRead.model_validate(event)


@router.get("", response_model=list[EventRead])
async def list_events(ctx: OrgMember, db: DbSession) -> list[EventRead]:
    events = await _service(db).list_for_org(ctx.organization)
    return [EventRead.model_validate(e) for e in events]


@router.get("/{event_id}", response_model=EventRead)
async def get_event(event_id: uuid.UUID, ctx: OrgMember, db: DbSession) -> EventRead:
    event = await _service(db).get_for_org(ctx.organization, event_id)
    return EventRead.model_validate(event)


@router.patch("/{event_id}", response_model=EventRead)
async def update_event(
    event_id: uuid.UUID, payload: EventUpdate, ctx: OrgMember, db: DbSession
) -> EventRead:
    service = _service(db)
    event = await service.get_for_org(ctx.organization, event_id)
    updated = await service.update(event, payload)
    return EventRead.model_validate(updated)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(event_id: uuid.UUID, ctx: OrgMember, db: DbSession) -> None:
    service = _service(db)
    event = await service.get_for_org(ctx.organization, event_id)
    await service.delete(event)


# ── Lifecycle transitions (dedicated business actions, not status PATCH) ──

_ACTIONS = {
    "preview": "to_preview",
    "submit": "submit_for_review",
    "publish": "publish",
    "hide": "hide",
    "unhide": "unhide",
    "cancel": "cancel",
    "archive": "archive",
}


def _register_action(action: str, method: str) -> None:
    @router.post(f"/{{event_id}}/{action}", response_model=EventRead, name=f"event_{action}")
    async def _handler(event_id: uuid.UUID, ctx: OrgMember, db: DbSession) -> EventRead:
        event = await _service(db).get_for_org(ctx.organization, event_id)
        updated = await getattr(_lifecycle(db), method)(event)
        return EventRead.model_validate(updated)


for _action, _method in _ACTIONS.items():
    _register_action(_action, _method)
