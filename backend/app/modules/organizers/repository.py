"""Data access for organizations and memberships."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.organizers.models import Organization, OrganizationMember


class OrganizationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def slug_exists(self, slug: str) -> bool:
        result = await self._db.execute(
            select(func.count()).select_from(Organization).where(Organization.slug == slug)
        )
        return (result.scalar() or 0) > 0

    async def get_by_slug(self, slug: str) -> Organization | None:
        result = await self._db.execute(select(Organization).where(Organization.slug == slug))
        return result.scalar_one_or_none()

    async def add(self, org: Organization) -> Organization:
        self._db.add(org)
        await self._db.flush()
        return org

    async def add_member(self, member: OrganizationMember) -> OrganizationMember:
        self._db.add(member)
        await self._db.flush()
        return member

    async def get_membership(
        self, organization_id: uuid.UUID, user_id: str
    ) -> OrganizationMember | None:
        result = await self._db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: str) -> list[tuple[Organization, str]]:
        result = await self._db.execute(
            select(Organization, OrganizationMember.role)
            .join(OrganizationMember, OrganizationMember.organization_id == Organization.id)
            .where(OrganizationMember.user_id == user_id)
            .order_by(Organization.created_at.desc())
        )
        return list(result.all())

    async def list_members(self, organization_id: uuid.UUID) -> list[OrganizationMember]:
        result = await self._db.execute(
            select(OrganizationMember).where(OrganizationMember.organization_id == organization_id)
        )
        return list(result.scalars().all())

    async def commit(self) -> None:
        await self._db.commit()

    async def rollback(self) -> None:
        await self._db.rollback()
