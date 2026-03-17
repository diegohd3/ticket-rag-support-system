"""create tickets table

Revision ID: 20260316_0001
Revises:
Create Date: 2026-03-16 10:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql


revision = "20260316_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "tickets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ticket_id", sa.String(length=64), nullable=False),
        sa.Column("titulo", sa.String(length=255), nullable=False),
        sa.Column("descripcion_problema", sa.Text(), nullable=False),
        sa.Column("descripcion_solucion", sa.Text(), nullable=False),
        sa.Column("categoria", sa.String(length=80), nullable=False),
        sa.Column("prioridad", sa.String(length=40), nullable=False),
        sa.Column("estado", sa.String(length=40), nullable=False),
        sa.Column(
            "fecha_creacion",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("fecha_cierre", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String(length=60)), nullable=False),
        sa.Column("usuario_creador", sa.String(length=120), nullable=False),
        sa.Column("sistema_afectado", sa.String(length=120), nullable=False),
        sa.Column(
            "logs",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("causa_raiz", sa.Text(), nullable=True),
        sa.Column("pasos_diagnostico", sa.Text(), nullable=True),
        sa.Column("entorno", sa.String(length=120), nullable=True),
        sa.Column("version_sistema", sa.String(length=80), nullable=True),
        sa.Column("impacto", sa.String(length=120), nullable=True),
        sa.Column(
            "resuelto_exitosamente",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(op.f("ix_tickets_id"), "tickets", ["id"], unique=False)
    op.create_index(op.f("ix_tickets_ticket_id"), "tickets", ["ticket_id"], unique=True)
    op.create_index(op.f("ix_tickets_titulo"), "tickets", ["titulo"], unique=False)
    op.create_index(op.f("ix_tickets_categoria"), "tickets", ["categoria"], unique=False)
    op.create_index(op.f("ix_tickets_prioridad"), "tickets", ["prioridad"], unique=False)
    op.create_index(op.f("ix_tickets_estado"), "tickets", ["estado"], unique=False)
    op.create_index(op.f("ix_tickets_fecha_creacion"), "tickets", ["fecha_creacion"], unique=False)
    op.create_index(op.f("ix_tickets_usuario_creador"), "tickets", ["usuario_creador"], unique=False)
    op.create_index(op.f("ix_tickets_sistema_afectado"), "tickets", ["sistema_afectado"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_tickets_sistema_afectado"), table_name="tickets")
    op.drop_index(op.f("ix_tickets_usuario_creador"), table_name="tickets")
    op.drop_index(op.f("ix_tickets_fecha_creacion"), table_name="tickets")
    op.drop_index(op.f("ix_tickets_estado"), table_name="tickets")
    op.drop_index(op.f("ix_tickets_prioridad"), table_name="tickets")
    op.drop_index(op.f("ix_tickets_categoria"), table_name="tickets")
    op.drop_index(op.f("ix_tickets_titulo"), table_name="tickets")
    op.drop_index(op.f("ix_tickets_ticket_id"), table_name="tickets")
    op.drop_index(op.f("ix_tickets_id"), table_name="tickets")
    op.drop_table("tickets")
