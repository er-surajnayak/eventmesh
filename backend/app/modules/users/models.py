"""User profile model.

``profiles.id`` mirrors Supabase ``auth.users.id``. Supabase owns identity;
this table holds application-level profile data and roles.
"""

import enum

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class UserRole(enum.StrEnum):
    registered = "registered"
    organizer = "organizer"
    moderator = "moderator"
    admin = "admin"
    super_admin = "super_admin"


class Profile(Base, TimestampMixin):
    __tablename__ = "profiles"

    # Equal to auth.users.id (Supabase). Not generated locally.
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    handle: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"), default=UserRole.registered, nullable=False
    )
    is_organizer: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
