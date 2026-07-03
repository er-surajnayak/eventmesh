"""User routes. Routers stay thin: resolve deps, delegate to the service, return."""

from fastapi import APIRouter

from app.api.v1.deps import CurrentUser, DbSession
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import ProfileRead
from app.modules.users.service import UserService

router = APIRouter(prefix="/users", tags=["users"])


def _service(db: DbSession) -> UserService:
    return UserService(UserRepository(db))


@router.get("/me", response_model=ProfileRead)
async def read_me(current_user: CurrentUser, db: DbSession) -> ProfileRead:
    """Return the caller's profile, provisioning it on first authenticated call."""
    profile = await _service(db).get_or_create_from_auth(current_user)
    return ProfileRead.model_validate(profile)
