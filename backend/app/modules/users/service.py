"""User domain business logic.

Cross-module access always goes service-to-service, never repository-to-repository.
"""

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError
from app.core.security import AuthUser
from app.modules.users.models import Profile, UserRole
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import ProfileUpdate


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

    async def update_profile(self, profile: Profile, data: ProfileUpdate) -> Profile:
        """Apply a partial profile update; ``handle`` is unique."""
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(profile, field, value)
        try:
            await self._repo.commit()
        except IntegrityError as exc:
            await self._repo.rollback()
            raise ConflictError("That handle is already taken.") from exc
        return profile

    async def become_organizer(self, profile: Profile) -> Profile:
        """Promote a registered user to organizer. Idempotent."""
        if not profile.is_organizer:
            profile.is_organizer = True
            if profile.role == UserRole.registered:
                profile.role = UserRole.organizer
            await self._repo.commit()
        return profile
