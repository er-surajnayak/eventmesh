"""org status and type

Revision ID: 57e5f1319551
Revises: 5a959eef2ae6
Create Date: 2026-07-03 14:40:42.175197+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "57e5f1319551"
down_revision: str | None = "5a959eef2ae6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    # Create the enum types explicitly (add_column does not auto-create them),
    # with create_type=False on the columns so they aren't created twice.
    org_status = postgresql.ENUM(
        "pending", "verified", "rejected", "suspended", name="org_status", create_type=False
    )
    org_type = postgresql.ENUM(
        "community",
        "company",
        "university",
        "ngo",
        "club",
        "other",
        name="org_type",
        create_type=False,
    )
    org_status.create(bind, checkfirst=True)
    org_type.create(bind, checkfirst=True)
    # server_default 'verified' makes the NOT NULL add safe on populated tables.
    op.add_column(
        "organizations",
        sa.Column("status", org_status, nullable=False, server_default="verified"),
    )
    op.add_column("organizations", sa.Column("type", org_type, nullable=True))


def downgrade() -> None:
    op.drop_column("organizations", "type")
    op.drop_column("organizations", "status")
    sa.Enum(name="org_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="org_status").drop(op.get_bind(), checkfirst=True)
