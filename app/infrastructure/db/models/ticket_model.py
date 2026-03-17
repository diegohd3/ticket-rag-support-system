from __future__ import annotations

from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import ARRAY, Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.config.settings import get_settings
from app.infrastructure.db.base import Base

settings = get_settings()


class TicketModel(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    ticket_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    titulo: Mapped[str] = mapped_column(String(255), index=True)
    descripcion_problema: Mapped[str] = mapped_column(Text)
    descripcion_solucion: Mapped[str] = mapped_column(Text)
    categoria: Mapped[str] = mapped_column(String(80), index=True)
    prioridad: Mapped[str] = mapped_column(String(40), index=True)
    estado: Mapped[str] = mapped_column(String(40), index=True)
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        index=True,
    )
    fecha_cierre: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String(60)), default=list)
    usuario_creador: Mapped[str] = mapped_column(String(120), index=True)
    sistema_afectado: Mapped[str] = mapped_column(String(120), index=True)
    logs: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    causa_raiz: Mapped[str | None] = mapped_column(Text, nullable=True)
    pasos_diagnostico: Mapped[str | None] = mapped_column(Text, nullable=True)
    entorno: Mapped[str | None] = mapped_column(String(120), nullable=True)
    version_sistema: Mapped[str | None] = mapped_column(String(80), nullable=True)
    impacto: Mapped[str | None] = mapped_column(String(120), nullable=True)
    resuelto_exitosamente: Mapped[bool] = mapped_column(Boolean, default=True)

    # Stored ticket vectors are used by pgvector semantic retrieval.
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(settings.embedding_dimension), nullable=True
    )
    embedding_model: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    embedding_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
