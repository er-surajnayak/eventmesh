"""Pydantic schemas for the events domain (3A: CRUD)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.events.models import (
    EventStatus,
    EventType,
    EventVisibility,
    RegistrationStatus,
)


class EventCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: str | None = None
    event_type: EventType = EventType.offline
    visibility: EventVisibility = EventVisibility.public
    start_time: datetime | None = None
    end_time: datetime | None = None
    timezone: str | None = Field(default=None, max_length=64)
    venue_name: str | None = None
    venue_address: str | None = None
    city: str | None = None
    country: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    is_free: bool = True
    price_cents: int | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    capacity: int | None = Field(default=None, ge=1)
    registration_required: bool = True
    registration_closes_at: datetime | None = None
    cover_image_url: str | None = None
    refund_policy: str | None = None


class EventUpdate(BaseModel):
    """Partial update of content fields. Status transitions are handled by
    dedicated lifecycle endpoints (3B), not here."""

    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = None
    event_type: EventType | None = None
    visibility: EventVisibility | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    timezone: str | None = Field(default=None, max_length=64)
    venue_name: str | None = None
    venue_address: str | None = None
    city: str | None = None
    country: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    is_free: bool | None = None
    price_cents: int | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    capacity: int | None = Field(default=None, ge=1)
    registration_required: bool | None = None
    registration_closes_at: datetime | None = None
    cover_image_url: str | None = None
    refund_policy: str | None = None


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    slug: str
    title: str
    description: str | None
    status: EventStatus
    event_type: EventType
    visibility: EventVisibility
    start_time: datetime | None
    end_time: datetime | None
    timezone: str | None
    venue_name: str | None
    venue_address: str | None
    city: str | None
    country: str | None
    latitude: float | None
    longitude: float | None
    is_free: bool
    price_cents: int | None
    currency: str | None
    capacity: int | None
    registration_required: bool
    registration_closes_at: datetime | None
    cover_image_url: str | None
    refund_policy: str | None
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime


class RegistrationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    native_event_id: uuid.UUID
    user_id: str
    status: RegistrationStatus
    created_at: datetime


class EventListResponse(BaseModel):
    total: int
    items: list[EventRead]
    next_offset: int | None = None


class VisibleEventRead(BaseModel):
    """A row of the visible read model (native or canonical-imported)."""

    model_config = ConfigDict(from_attributes=True)

    kind: str  # native | imported
    id: uuid.UUID
    slug: str | None
    title: str
    description: str | None
    image_url: str | None
    start_time: datetime
    end_time: datetime | None
    timezone: str | None
    city: str | None
    venue: str | None
    is_online: bool
    is_free: bool
    price_cents: int | None
    currency: str | None
    category: str | None
    url: str | None  # imported: source URL (click-through); native: None
    provider: str  # 'eventmesh' or a source slug
    sources: list[str]  # provenance: every provider in the canonical group
    organization_id: uuid.UUID | None


class VisibleListResponse(BaseModel):
    total: int
    items: list[VisibleEventRead]
    next_offset: int | None = None
