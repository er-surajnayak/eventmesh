"""Authorization dependencies for the organizers domain."""

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends

from app.api.v1.deps import DbSession
from app.core.exceptions import ForbiddenError
from app.modules.organizers.models import Organization, OrganizationMember
from app.modules.organizers.repository import OrganizationRepository
from app.modules.organizers.service import OrganizationService
from app.modules.users.dependencies import CurrentProfile


@dataclass
class OrgContext:
    organization: Organization
    membership: OrganizationMember


async def require_org_member(slug: str, profile: CurrentProfile, db: DbSession) -> OrgContext:
    repo = OrganizationRepository(db)
    org = await OrganizationService(repo).get_by_slug(slug)
    membership = await repo.get_membership(org.id, profile.id)
    if membership is None:
        raise ForbiddenError("You are not a member of this organization.")
    return OrgContext(organization=org, membership=membership)


OrgMember = Annotated[OrgContext, Depends(require_org_member)]
