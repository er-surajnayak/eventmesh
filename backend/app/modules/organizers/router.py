"""Organization routes."""

from fastapi import APIRouter, status

from app.api.v1.deps import DbSession
from app.modules.organizers.dependencies import OrgMember
from app.modules.organizers.models import OrgRole
from app.modules.organizers.repository import OrganizationRepository
from app.modules.organizers.schemas import MemberRead, OrganizationCreate, OrganizationRead
from app.modules.organizers.service import OrganizationService
from app.modules.users.dependencies import CurrentProfile, RequireOrganizer

router = APIRouter(prefix="/organizations", tags=["organizations"])


def _service(db: DbSession) -> OrganizationService:
    return OrganizationService(OrganizationRepository(db))


@router.post("", response_model=OrganizationRead, status_code=status.HTTP_201_CREATED)
async def create_organization(
    payload: OrganizationCreate, organizer: RequireOrganizer, db: DbSession
) -> OrganizationRead:
    org = await _service(db).create_organization(organizer, payload)
    read = OrganizationRead.model_validate(org)
    read.role = OrgRole.owner
    return read


@router.get("", response_model=list[OrganizationRead])
async def list_my_organizations(profile: CurrentProfile, db: DbSession) -> list[OrganizationRead]:
    rows = await _service(db).list_for_user(profile.id)
    result: list[OrganizationRead] = []
    for org, role in rows:
        read = OrganizationRead.model_validate(org)
        read.role = role
        result.append(read)
    return result


@router.get("/{slug}", response_model=OrganizationRead)
async def get_organization(slug: str, db: DbSession) -> OrganizationRead:
    org = await _service(db).get_by_slug(slug)
    return OrganizationRead.model_validate(org)


@router.get("/{slug}/members", response_model=list[MemberRead])
async def list_members(ctx: OrgMember, db: DbSession) -> list[MemberRead]:
    members = await _service(db).list_members(ctx.organization)
    return [MemberRead.model_validate(m) for m in members]
