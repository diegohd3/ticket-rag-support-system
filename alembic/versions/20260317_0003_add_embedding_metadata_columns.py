"""add embedding metadata columns

Revision ID: 20260317_0003
Revises: 20260316_0002
Create Date: 2026-03-17 16:10:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260317_0003"
down_revision = "20260316_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tickets",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.add_column(
        "tickets",
        sa.Column("embedding_model", sa.String(length=120), nullable=True),
    )
    op.add_column(
        "tickets",
        sa.Column("embedding_updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index(op.f("ix_tickets_updated_at"), "tickets", ["updated_at"], unique=False)
    op.create_index(
        op.f("ix_tickets_embedding_updated_at"),
        "tickets",
        ["embedding_updated_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_tickets_embedding_model"),
        "tickets",
        ["embedding_model"],
        unique=False,
    )

    # Existing rows with vectors are treated as indexed at migration time.
    op.execute(
        """
        UPDATE tickets
        SET embedding_updated_at = now()
        WHERE embedding IS NOT NULL AND embedding_updated_at IS NULL
        """
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_tickets_embedding_model"), table_name="tickets")
    op.drop_index(op.f("ix_tickets_embedding_updated_at"), table_name="tickets")
    op.drop_index(op.f("ix_tickets_updated_at"), table_name="tickets")
    op.drop_column("tickets", "embedding_updated_at")
    op.drop_column("tickets", "embedding_model")
    op.drop_column("tickets", "updated_at")
