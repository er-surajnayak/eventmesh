"""Organizer domain business logic."""

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, NotFoundError
from app.modules.organizers.models import Organization, OrganizationMember, OrgRole
from app.modules.organizers.repository import OrganizationRepository
from app.modules.organizers.schemas import OrganizationCreate
from app.modules.organizers.slug import slugify
from app.modules.users.models import Profile

_MAX_SLUG_ATTEMPTS = 50


class OrganizationService:
    def __init__(self, repository: OrganizationRepository) -> None:
        self._repo = repository

    async def _unique_slug(self, base: str) -> str:
        root = slugify(base)
        candidate = root
        suffix = 2
        while await self._repo.slug_exists(candidate):
            candidate = f"{root}-{suffix}"
            suffix += 1
            if suffix > _MAX_SLUG_ATTEMPTS:
                # Extremely unlikely; fall back to a root that includes the count.
                candidate = f"{root}-{suffix}"
                break
        return candidate

    async def create_organization(self, owner: Profile, data: OrganizationCreate) -> Organization:
        slug = await self._unique_slug(data.slug or data.name)
        org = Organization(
            owner_id=owner.id,
            slug=slug,
            name=data.name,
            description=data.description,
            website=data.website,
            type=data.type,
        )
        try:
            await self._repo.add(org)
            await self._repo.add_member(
                OrganizationMember(organization_id=org.id, user_id=owner.id, role=OrgRole.owner)
            )
            await self._repo.commit()
        except IntegrityError as exc:
            await self._repo.rollback()
            raise ConflictError("Could not create organization (slug already taken).") from exc
        return org

    async def get_by_slug(self, slug: str) -> Organization:
        org = await self._repo.get_by_slug(slug)
        if org is None:
            raise NotFoundError("Organization not found.")
        return org

    async def list_for_user(self, user_id: str) -> list[tuple[Organization, str]]:
        return await self._repo.list_for_user(user_id)

    async def list_members(self, org: Organization) -> list[OrganizationMember]:
        return await self._repo.list_members(org.id)
