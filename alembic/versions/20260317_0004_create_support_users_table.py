"""create support users table

Revision ID: 20260317_0004
Revises: 20260317_0003
Create Date: 2026-03-17 12:20:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260317_0004"
down_revision = "20260317_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "support_users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(length=120), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=True),
        sa.Column(
            "is_blocked",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "violation_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("blocked_reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("blocked_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(op.f("ix_support_users_user_id"), "support_users", ["user_id"], unique=True)
    op.create_index(
        op.f("ix_support_users_is_blocked"),
        "support_users",
        ["is_blocked"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_support_users_is_blocked"), table_name="support_users")
    op.drop_index(op.f("ix_support_users_user_id"), table_name="support_users")
    op.drop_table("support_users")
