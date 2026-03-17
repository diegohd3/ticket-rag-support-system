from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.application.interfaces.ticket_repository import TicketRepository
from app.application.services.ticket_embedding_service import TicketEmbeddingService
from app.domain.entities.ticket import Ticket


@dataclass(slots=True)
class TicketCreateInput:
    titulo: str
    descripcion_problema: str
    descripcion_solucion: str
    categoria: str
    prioridad: str
    estado: str
    tags: list[str]
    usuario_creador: str
    sistema_afectado: str
    logs: dict
    causa_raiz: str | None = None
    pasos_diagnostico: str | None = None
    entorno: str | None = None
    version_sistema: str | None = None
    impacto: str | None = None
    resuelto_exitosamente: bool = True
    fecha_cierre: datetime | None = None
    ticket_id: str | None = None


@dataclass(slots=True)
class TicketCreateResult:
    ticket: Ticket
    embedding_created: bool


@dataclass(slots=True)
class TicketUpdateInput:
    titulo: str | None = None
    descripcion_problema: str | None = None
    descripcion_solucion: str | None = None
    categoria: str | None = None
    prioridad: str | None = None
    estado: str | None = None
    tags: list[str] | None = None
    usuario_creador: str | None = None
    sistema_afectado: str | None = None
    logs: dict[str, Any] | None = None
    causa_raiz: str | None = None
    pasos_diagnostico: str | None = None
    entorno: str | None = None
    version_sistema: str | None = None
    impacto: str | None = None
    resuelto_exitosamente: bool | None = None
    fecha_cierre: datetime | None = None
    provided_fields: set[str] = field(default_factory=set, repr=False)

    def to_update_map(self) -> dict[str, Any]:
        fields = {
            "titulo": self.titulo,
            "descripcion_problema": self.descripcion_problema,
            "descripcion_solucion": self.descripcion_solucion,
            "categoria": self.categoria,
            "prioridad": self.prioridad,
            "estado": self.estado,
            "tags": self.tags,
            "usuario_creador": self.usuario_creador,
            "sistema_afectado": self.sistema_afectado,
            "logs": self.logs,
            "causa_raiz": self.causa_raiz,
            "pasos_diagnostico": self.pasos_diagnostico,
            "entorno": self.entorno,
            "version_sistema": self.version_sistema,
            "impacto": self.impacto,
            "resuelto_exitosamente": self.resuelto_exitosamente,
            "fecha_cierre": self.fecha_cierre,
        }
        if self.provided_fields:
            return {
                key: fields[key]
                for key in self.provided_fields
                if key in fields
            }
        return {key: value for key, value in fields.items() if value is not None}

    @classmethod
    def from_partial(cls, payload: dict[str, Any]) -> "TicketUpdateInput":
        return cls(**payload, provided_fields=set(payload.keys()))


@dataclass(slots=True)
class TicketUpdateResult:
    ticket: Ticket
    embedding_refreshed: bool
    updated_fields: list[str]


class TicketIngestionService:
    EMBEDDING_FIELDS = frozenset(
        {
            "titulo",
            "descripcion_problema",
            "descripcion_solucion",
            "categoria",
            "tags",
            "sistema_afectado",
            "logs",
            "causa_raiz",
            "pasos_diagnostico",
        }
    )

    def __init__(
        self,
        repository: TicketRepository,
        embedding_service: TicketEmbeddingService,
    ) -> None:
        self._repository = repository
        self._embedding_service = embedding_service

    def create_ticket(
        self,
        payload: TicketCreateInput,
        auto_embed: bool = True,
    ) -> TicketCreateResult:
        ticket = Ticket(
            ticket_id=payload.ticket_id or self._generate_ticket_id(),
            titulo=payload.titulo,
            descripcion_problema=payload.descripcion_problema,
            descripcion_solucion=payload.descripcion_solucion,
            categoria=payload.categoria,
            prioridad=payload.prioridad,
            estado=payload.estado,
            fecha_creacion=datetime.now(UTC),
            fecha_cierre=payload.fecha_cierre,
            tags=payload.tags,
            usuario_creador=payload.usuario_creador,
            sistema_afectado=payload.sistema_afectado,
            logs=payload.logs,
            causa_raiz=payload.causa_raiz,
            pasos_diagnostico=payload.pasos_diagnostico,
            entorno=payload.entorno,
            version_sistema=payload.version_sistema,
            impacto=payload.impacto,
            resuelto_exitosamente=payload.resuelto_exitosamente,
        )
        created = self._repository.create_ticket(ticket)
        embedding_created = (
            self._embedding_service.update_ticket_embedding(created) if auto_embed else False
        )
        return TicketCreateResult(ticket=created, embedding_created=embedding_created)

    def update_ticket(
        self,
        ticket_id: str,
        payload: TicketUpdateInput,
        auto_embed: bool = True,
    ) -> TicketUpdateResult | None:
        update_fields = payload.to_update_map()
        if not update_fields:
            existing = self._repository.get_ticket_by_ticket_id(ticket_id)
            if not existing:
                return None
            return TicketUpdateResult(ticket=existing, embedding_refreshed=False, updated_fields=[])

        updated_ticket = self._repository.update_ticket_fields(ticket_id, update_fields)
        if not updated_ticket:
            return None

        should_refresh_embedding = auto_embed and any(
            field in self.EMBEDDING_FIELDS for field in update_fields
        )
        embedding_refreshed = (
            self._embedding_service.update_ticket_embedding(updated_ticket)
            if should_refresh_embedding
            else False
        )
        return TicketUpdateResult(
            ticket=updated_ticket,
            embedding_refreshed=embedding_refreshed,
            updated_fields=sorted(update_fields.keys()),
        )

    @staticmethod
    def _generate_ticket_id() -> str:
        return f"TCK-{uuid4().hex[:8].upper()}"
