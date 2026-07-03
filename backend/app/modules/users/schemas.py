"""Pydantic schemas for the users domain."""

from pydantic import BaseModel, ConfigDict

from app.modules.users.models import UserRole


class ProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str | None = None
    handle: str | None = None
    display_name: str | None = None
    avatar_url: str | None = None
    role: UserRole
    is_organizer: bool


class ProfileUpdate(BaseModel):
    handle: str | None = None
    display_name: str | None = None
    avatar_url: str | None = None
