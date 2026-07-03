"""Native (EventMesh-hosted) event model.

The table is ``native_events`` to keep the V2 Native/Imported/Visible separation
clear once aggregated events arrive (Phase 4). The full lifecycle/field set lives
here in 3A; transitions and registration logic land in 3B.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class EventStatus(enum.StrEnum):
    draft = "draft"
    preview = "preview"
    pending_review = "pending_review"
    published = "published"
    hidden = "hidden"
    cancelled = "cancelled"
    archived = "archived"


class EventType(enum.StrEnum):
    online = "online"
    offline = "offline"
    hybrid = "hybrid"


class EventVisibility(enum.StrEnum):
    public = "public"
    private = "private"
    unlisted = "unlisted"


class NativeEvent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "native_events"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[EventStatus] = mapped_column(
        Enum(EventStatus, name="event_status"),
        nullable=False,
        default=EventStatus.draft,
        index=True,
    )
    event_type: Mapped[EventType] = mapped_column(
        Enum(EventType, name="event_type"), nullable=False, default=EventType.offline
    )
    visibility: Mapped[EventVisibility] = mapped_column(
        Enum(EventVisibility, name="event_visibility"),
        nullable=False,
        default=EventVisibility.public,
    )

    # Timing (nullable while a draft is incomplete; enforced at publish in 3B).
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Location.
    venue_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    venue_address: Mapped[str | None] = mapped_column(String(400), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    country: Mapped[str | None] = mapped_column(String(120), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Pricing.
    is_free: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    price_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)

    # Registration & capacity (logic in 3B; fields defined now).
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    registration_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    registration_closes_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Media (URL-only per the no-upload MVP; a future event_media table can
    # generalize this to multiple images without reshaping native_events).
    cover_image_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    # Policies.
    refund_policy: Mapped[str | None] = mapped_column(Text, nullable=True)
