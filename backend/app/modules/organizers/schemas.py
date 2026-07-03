"""Pydantic schemas for the organizers domain."""

import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.modules.organizers.models import OrgRole, OrgStatus, OrgType


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    slug: str | None = Field(default=None, max_length=80)
    description: str | None = None
    website: str | None = None
    type: OrgType | None = None


class OrganizationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    name: str
    description: str | None = None
    website: str | None = None
    avatar_url: str | None = None
    owner_id: str
    status: OrgStatus
    type: OrgType | None = None
    # The requesting user's role in this org, when known (None for public reads).
    role: OrgRole | None = None


class MemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    role: OrgRole
