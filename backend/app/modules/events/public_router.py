"""Public event browsing + registration.

Visibility rules for public reads: only ``published`` events are visible, and
``private`` events are never exposed here (``unlisted`` is reachable by direct
slug but excluded from listings).
"""

from fastapi import APIRouter, status

from app.api.v1.deps import DbSession, Pagination
from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.pagination import Page
from app.modules.events.models import EventStatus, EventVisibility, NativeEvent
from app.modules.events.registration import RegistrationService
from app.modules.events.registration_repository import RegistrationRepository
from app.modules.events.repository import EventRepository
from app.modules.events.schemas import EventListResponse, EventRead, RegistrationRead
from app.modules.organizers.repository import OrganizationRepository
from app.modules.users.dependencies import CurrentProfile

router = APIRouter(tags=["events-public"])


def _registrations(db: DbSession) -> RegistrationService:
    return RegistrationService(RegistrationRepository(db))


async def _public_event(db: DbSession, slug: str) -> NativeEvent:
    event = await EventRepository(db).get_by_slug(slug)
    if (
        event is None
        or event.status != EventStatus.published
        or event.visibility == EventVisibility.private
    ):
        raise NotFoundError("Event not found.")
    return event


@router.get("/events", response_model=EventListResponse)
async def browse_events(page: Pagination, db: DbSession) -> EventListResponse:
    total, events = await EventRepository(db).list_public(limit=page.limit, offset=page.offset)
    built = Page.build(total=total, items=events, params=page)
    return EventListResponse(
        total=total,
        items=[EventRead.model_validate(e) for e in events],
        next_offset=built.next_offset,
    )


@router.get("/events/{slug}", response_model=EventRead)
async def get_public_event(slug: str, db: DbSession) -> EventRead:
    event = await _public_event(db, slug)
    return EventRead.model_validate(event)


@router.post("/events/{slug}/register", response_model=RegistrationRead)
async def register_for_event(slug: str, profile: CurrentProfile, db: DbSession) -> RegistrationRead:
    event = await _public_event(db, slug)
    registration = await _registrations(db).register(event, profile.id)
    return RegistrationRead.model_validate(registration)


@router.delete("/events/{slug}/register", response_model=RegistrationRead)
async def cancel_registration(
    slug: str, profile: CurrentProfile, db: DbSession
) -> RegistrationRead:
    event = await _public_event(db, slug)
    registration = await _registrations(db).cancel(event, profile.id)
    return RegistrationRead.model_validate(registration)


@router.get("/events/{slug}/registrations", response_model=list[RegistrationRead])
async def list_event_registrations(
    slug: str, profile: CurrentProfile, db: DbSession
) -> list[RegistrationRead]:
    event = await EventRepository(db).get_by_slug(slug)
    if event is None:
        raise NotFoundError("Event not found.")
    membership = await OrganizationRepository(db).get_membership(event.organization_id, profile.id)
    if membership is None:
        raise ForbiddenError("Only organizers can view the attendee list.")
    registrations = await _registrations(db).list_for_event(event)
    return [RegistrationRead.model_validate(r) for r in registrations]


@router.get("/registrations", response_model=list[RegistrationRead], status_code=status.HTTP_200_OK)
async def my_registrations(profile: CurrentProfile, db: DbSession) -> list[RegistrationRead]:
    registrations = await _registrations(db).list_for_user(profile.id)
    return [RegistrationRead.model_validate(r) for r in registrations]
