"""Organization and membership models.

Multi-member from the start: ``organization_members`` is a join table with a
role. Only ``owner`` is exposed today; the ``org_role`` enum is the extension
point for future roles (admin, editor, viewer, …).
"""

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class OrgRole(enum.StrEnum):
    owner = "owner"
    # Future (architecture-ready, not yet exposed): admin, editor, viewer


class OrgStatus(enum.StrEnum):
    pending = "pending"
    verified = "verified"
    rejected = "rejected"
    suspended = "suspended"


class OrgType(enum.StrEnum):
    community = "community"
    company = "company"
    university = "university"
    ngo = "ngo"
    club = "club"
    other = "other"


class Organization(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "organizations"

    owner_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    website: Mapped[str | None] = mapped_column(String(512), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    # MVP auto-verifies; the field exists for future moderation.
    status: Mapped[OrgStatus] = mapped_column(
        Enum(OrgStatus, name="org_status"), nullable=False, default=OrgStatus.verified
    )
    # Optional; future-proofs filtering & discovery.
    type: Mapped[OrgType | None] = mapped_column(Enum(OrgType, name="org_type"), nullable=True)


class OrganizationMember(Base, TimestampMixin):
    __tablename__ = "organization_members"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[OrgRole] = mapped_column(
        Enum(OrgRole, name="org_role"), nullable=False, default=OrgRole.owner
    )
