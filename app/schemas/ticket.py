from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TicketCreateRequest(BaseModel):
    ticket_id: str | None = None
    titulo: str = Field(min_length=3)
    descripcion_problema: str = Field(min_length=10)
    descripcion_solucion: str = Field(min_length=5)
    categoria: str
    prioridad: str = "media"
    estado: str = "abierto"
    tags: list[str] = Field(default_factory=list)
    usuario_creador: str
    sistema_afectado: str
    logs: dict[str, Any] = Field(default_factory=dict)
    causa_raiz: str | None = None
    pasos_diagnostico: str | None = None
    entorno: str | None = None
    version_sistema: str | None = None
    impacto: str | None = None
    resuelto_exitosamente: bool = True
    fecha_cierre: datetime | None = None
    auto_embed: bool = True


class TicketCreateResponse(BaseModel):
    ticket: "TicketResponse"
    embedding_created: bool


class EmbeddingReindexResponse(BaseModel):
    processed: int
    updated: int
    failed: int
    failures: list[str] = Field(default_factory=list)


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
    text_score: float | None = Field(default=None)
    semantic_score: float | None = Field(default=None)
    rerank_score: float | None = Field(default=None)


TicketCreateResponse.model_rebuild()
