"""User domain business logic.

Cross-module access always goes service-to-service, never repository-to-repository.
"""

from sqlalchemy.exc import IntegrityError

from app.core.security import AuthUser
from app.modules.users.models import Profile
from app.modules.users.repository import UserRepository


class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self._repo = repository

    async def get_or_create_from_auth(self, auth_user: AuthUser) -> Profile:
        """Just-in-time profile provisioning from a verified JWT identity.

        Tolerant of a race where two concurrent first requests both insert.
        """
        existing = await self._repo.get(auth_user.id)
        if existing is not None:
            return existing

        profile = Profile(id=auth_user.id, email=auth_user.email)
        try:
            await self._repo.add(profile)
            await self._repo.commit()
            return profile
        except IntegrityError:
            await self._repo.rollback()
            winner = await self._repo.get(auth_user.id)
            if winner is None:
                raise
            return winner
