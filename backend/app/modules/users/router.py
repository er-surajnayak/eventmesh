"""User routes. Routers stay thin: resolve deps, delegate to the service, return."""

from fastapi import APIRouter

from app.api.v1.deps import DbSession
from app.modules.users.dependencies import CurrentProfile
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import ProfileRead, ProfileUpdate
from app.modules.users.service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=ProfileRead)
async def read_me(profile: CurrentProfile) -> ProfileRead:
    """Return the caller's profile (JIT-provisioned on first authenticated call)."""
    return ProfileRead.model_validate(profile)


@router.patch("/me", response_model=ProfileRead)
async def update_me(payload: ProfileUpdate, profile: CurrentProfile, db: DbSession) -> ProfileRead:
    """Update the caller's own profile."""
    service = UserService(UserRepository(db))
    updated = await service.update_profile(profile, payload)
    return ProfileRead.model_validate(updated)
