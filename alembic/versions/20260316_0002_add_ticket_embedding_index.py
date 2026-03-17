"""add ticket embedding index

Revision ID: 20260316_0002
Revises: 20260316_0001
Create Date: 2026-03-16 11:00:00.000000
"""

from __future__ import annotations

from alembic import op

revision = "20260316_0002"
down_revision = "20260316_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_tickets_embedding_cosine
        ON tickets
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_tickets_embedding_cosine")
