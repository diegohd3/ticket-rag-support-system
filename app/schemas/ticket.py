from __future__ import annotations

import json
from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

MAX_TEXT_FIELD_LENGTH = 4000
MAX_LOGS_JSON_LENGTH = 12000
MAX_TAGS_PER_TICKET = 50
Tag = Annotated[str, StringConstraints(min_length=1, max_length=60)]


class TicketCreateRequest(BaseModel):
    ticket_id: str | None = None
    titulo: str = Field(min_length=3, max_length=255)
    descripcion_problema: str = Field(min_length=10, max_length=MAX_TEXT_FIELD_LENGTH)
    descripcion_solucion: str = Field(min_length=5, max_length=MAX_TEXT_FIELD_LENGTH)
    categoria: str = Field(max_length=80)
    prioridad: str = Field(default="media", max_length=40)
    estado: str = Field(default="abierto", max_length=40)
    tags: list[Tag] = Field(default_factory=list, max_length=MAX_TAGS_PER_TICKET)
    usuario_creador: str = Field(max_length=120)
    sistema_afectado: str = Field(max_length=120)
    logs: dict[str, Any] = Field(default_factory=dict)
    causa_raiz: str | None = Field(default=None, max_length=MAX_TEXT_FIELD_LENGTH)
    pasos_diagnostico: str | None = Field(default=None, max_length=MAX_TEXT_FIELD_LENGTH)
    entorno: str | None = Field(default=None, max_length=120)
    version_sistema: str | None = Field(default=None, max_length=80)
    impacto: str | None = Field(default=None, max_length=120)
    resuelto_exitosamente: bool = True
    fecha_cierre: datetime | None = None
    auto_embed: bool = True

    @model_validator(mode="after")
    def validate_logs_size(self) -> "TicketCreateRequest":
        serialized = json.dumps(self.logs, ensure_ascii=False, default=str)
        if len(serialized) > MAX_LOGS_JSON_LENGTH:
            raise ValueError(
                f"logs payload exceeds maximum size of {MAX_LOGS_JSON_LENGTH} characters."
            )
        return self


class TicketCreateResponse(BaseModel):
    ticket: "TicketResponse"
    embedding_created: bool


class TicketUpdateRequest(BaseModel):
    titulo: str | None = Field(default=None, min_length=3, max_length=255)
    descripcion_problema: str | None = Field(
        default=None,
        min_length=10,
        max_length=MAX_TEXT_FIELD_LENGTH,
    )
    descripcion_solucion: str | None = Field(
        default=None,
        min_length=5,
        max_length=MAX_TEXT_FIELD_LENGTH,
    )
    categoria: str | None = Field(default=None, max_length=80)
    prioridad: str | None = Field(default=None, max_length=40)
    estado: str | None = Field(default=None, max_length=40)
    tags: list[Tag] | None = Field(default=None, max_length=MAX_TAGS_PER_TICKET)
    usuario_creador: str | None = Field(default=None, max_length=120)
    sistema_afectado: str | None = Field(default=None, max_length=120)
    logs: dict[str, Any] | None = None
    causa_raiz: str | None = Field(default=None, max_length=MAX_TEXT_FIELD_LENGTH)
    pasos_diagnostico: str | None = Field(default=None, max_length=MAX_TEXT_FIELD_LENGTH)
    entorno: str | None = Field(default=None, max_length=120)
    version_sistema: str | None = Field(default=None, max_length=80)
    impacto: str | None = Field(default=None, max_length=120)
    resuelto_exitosamente: bool | None = None
    fecha_cierre: datetime | None = None
    auto_embed: bool = True

    @model_validator(mode="after")
    def validate_logs_size(self) -> "TicketUpdateRequest":
        if self.logs is None:
            return self
        serialized = json.dumps(self.logs, ensure_ascii=False, default=str)
        if len(serialized) > MAX_LOGS_JSON_LENGTH:
            raise ValueError(
                f"logs payload exceeds maximum size of {MAX_LOGS_JSON_LENGTH} characters."
            )
        return self


class TicketUpdateResponse(BaseModel):
    ticket: "TicketResponse"
    embedding_refreshed: bool
    updated_fields: list[str] = Field(default_factory=list)


class EmbeddingReindexResponse(BaseModel):
    mode: str
    processed: int
    updated: int
    failed: int
    failures: list[str] = Field(default_factory=list)


class TicketListResponse(BaseModel):
    items: list["TicketResponse"]
    total: int
    limit: int
    offset: int
    has_next: bool


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
TicketUpdateResponse.model_rebuild()
TicketListResponse.model_rebuild()
