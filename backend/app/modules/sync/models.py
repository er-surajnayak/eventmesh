"""Aggregation data model: imported events + sync runs.

Imported events are NEVER exposed directly; they surface only through the
visible read model once canonical + active (wired in 4E). Kept separate from
native_events per the V2 Native/Imported/Visible separation.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class ImportedStatus(enum.StrEnum):
    active = "active"
    expired = "expired"
    suppressed = "suppressed"


class SyncStatus(enum.StrEnum):
    running = "running"
    success = "success"
    partial = "partial"
    failed = "failed"


class ImportedEvent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "imported_events"
    __table_args__ = (
        UniqueConstraint("provider", "external_id", name="uq_imported_provider_external"),
    )

    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(200), nullable=False)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    venue: Mapped[str | None] = mapped_column(String(300), nullable=True)
    is_online: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_free: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    price_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    category: Mapped[str | None] = mapped_column(String(80), nullable=True)

    # Deduplication.
    dedup_hash: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    canonical_group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    is_canonical: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    status: Mapped[ImportedStatus] = mapped_column(
        Enum(ImportedStatus, name="imported_status"),
        nullable=False,
        default=ImportedStatus.active,
        index=True,
    )
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SyncRun(Base, UUIDMixin):
    __tablename__ = "sync_runs"

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[SyncStatus] = mapped_column(Enum(SyncStatus, name="sync_status"), nullable=False)
    totals: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
