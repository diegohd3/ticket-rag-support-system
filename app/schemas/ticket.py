from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ticket_id: str
    titulo: str
    descripcion_problema: str
    descripcion_solucion: str
    categoria: str
    prioridad: str
    estado: str
    fecha_creacion: datetime
    fecha_cierre: datetime | None
    tags: list[str]
    usuario_creador: str
    sistema_afectado: str
    logs: dict[str, Any]
    causa_raiz: str | None = None
    pasos_diagnostico: str | None = None
    entorno: str | None = None
    version_sistema: str | None = None
    impacto: str | None = None
    resuelto_exitosamente: bool = True
    relevance_score: float | None = Field(default=None)
