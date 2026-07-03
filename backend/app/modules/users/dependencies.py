"""Auth/authorization dependencies for the users domain.

- ``get_current_profile`` resolves the app profile for a verified JWT identity
  (JIT-provisioning on first call).
- ``require_roles`` gates a route on the caller's application role.

Application roles live on ``profiles.role`` (the Supabase JWT only carries the
generic ``authenticated`` role), so role checks require a DB-loaded profile.
"""

from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends

from app.api.v1.deps import CurrentUser, DbSession
from app.core.exceptions import ForbiddenError
from app.modules.users.models import Profile, UserRole
from app.modules.users.repository import UserRepository
from app.modules.users.service import UserService


def _service(db: DbSession) -> UserService:
    return UserService(UserRepository(db))


async def get_current_profile(current_user: CurrentUser, db: DbSession) -> Profile:
    return await _service(db).get_or_create_from_auth(current_user)


CurrentProfile = Annotated[Profile, Depends(get_current_profile)]


def require_roles(*roles: UserRole) -> Callable[[Profile], Awaitable[Profile]]:
    """Dependency factory: allow only the given application roles."""
    allowed = set(roles)

    async def _guard(profile: CurrentProfile) -> Profile:
        if profile.role not in allowed:
            raise ForbiddenError("Insufficient role for this action.")
        return profile

    return _guard


# Convenience guards for common privilege tiers.
require_moderator = require_roles(UserRole.moderator, UserRole.admin, UserRole.super_admin)
require_admin = require_roles(UserRole.admin, UserRole.super_admin)
require_super_admin = require_roles(UserRole.super_admin)


async def require_organizer(profile: CurrentProfile) -> Profile:
    """Allow only users who have completed the 'Become Organizer' step."""
    if not profile.is_organizer:
        raise ForbiddenError("You must become an organizer before creating an organization.")
    return profile


RequireOrganizer = Annotated[Profile, Depends(require_organizer)]
