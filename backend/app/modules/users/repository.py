"""Data access for user profiles. No business logic lives here."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import Profile


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get(self, user_id: str) -> Profile | None:
        result = await self._db.execute(select(Profile).where(Profile.id == user_id))
        return result.scalar_one_or_none()

    async def add(self, profile: Profile) -> Profile:
        self._db.add(profile)
        await self._db.flush()
        return profile

    async def commit(self) -> None:
        await self._db.commit()

    async def rollback(self) -> None:
        await self._db.rollback()
