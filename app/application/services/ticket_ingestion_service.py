from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
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


class TicketIngestionService:
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

    @staticmethod
    def _generate_ticket_id() -> str:
        return f"TCK-{uuid4().hex[:8].upper()}"
