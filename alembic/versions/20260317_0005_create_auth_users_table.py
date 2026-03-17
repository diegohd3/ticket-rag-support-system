"""create auth users table

Revision ID: 20260317_0005
Revises: 20260317_0004
Create Date: 2026-03-17 16:10:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260317_0005"
down_revision = "20260317_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "auth_users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.text("false")),
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
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(op.f("ix_auth_users_username"), "auth_users", ["username"], unique=True)
    op.create_index(op.f("ix_auth_users_is_active"), "auth_users", ["is_active"], unique=False)
    op.create_index(op.f("ix_auth_users_is_admin"), "auth_users", ["is_admin"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_auth_users_is_admin"), table_name="auth_users")
    op.drop_index(op.f("ix_auth_users_is_active"), table_name="auth_users")
    op.drop_index(op.f("ix_auth_users_username"), table_name="auth_users")
    op.drop_table("auth_users")
