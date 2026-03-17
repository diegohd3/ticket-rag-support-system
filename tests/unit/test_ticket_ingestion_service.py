from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.application.interfaces.ticket_repository import TicketRepository
from app.application.services.ticket_ingestion_service import (
    TicketIngestionService,
    TicketUpdateInput,
)
from app.domain.entities.ticket import Ticket
from app.domain.value_objects.search_filters import SearchFilters
from app.domain.value_objects.search_query import SearchQuery


def _ticket(ticket_id: str = "TCK-1") -> Ticket:
    return Ticket(
        ticket_id=ticket_id,
        titulo="Titulo",
        descripcion_problema="Problema descriptivo",
        descripcion_solucion="Solucion",
        categoria="backend",
        prioridad="media",
        estado="abierto",
        fecha_creacion=datetime.now(UTC),
        fecha_cierre=None,
        tags=["tag1"],
        usuario_creador="qa",
        sistema_afectado="api",
        logs={"error": "E1"},
        causa_raiz=None,
        pasos_diagnostico=None,
        entorno=None,
        version_sistema=None,
        impacto=None,
        resuelto_exitosamente=True,
    )


class FakeRepository(TicketRepository):
    def __init__(self) -> None:
        self.ticket = _ticket()

    def count_tickets(self) -> int:
        return 1

    def list_tickets(self, limit: int, offset: int) -> list[Ticket]:
        return [self.ticket][offset : offset + limit]

    def get_ticket_by_ticket_id(self, ticket_id: str) -> Ticket | None:
        return self.ticket if ticket_id == self.ticket.ticket_id else None

    def search_candidates(self, query: SearchQuery, limit: int) -> list[Ticket]:
        return []

    def semantic_search(
        self,
        query_embedding: list[float],
        limit: int,
        filters: SearchFilters | None = None,
    ) -> list[tuple[Ticket, float]]:
        return []

    def list_tickets_without_embeddings(self, limit: int, offset: int = 0) -> list[Ticket]:
        return []

    def list_tickets_with_stale_embeddings(
        self,
        limit: int,
        embedding_model: str,
        offset: int = 0,
    ) -> list[Ticket]:
        return []

    def update_ticket_embedding(
        self,
        ticket_id: str,
        embedding: list[float],
        embedding_model: str,
    ) -> bool:
        return True

    def create_ticket(self, ticket: Ticket) -> Ticket:
        return ticket

    def update_ticket_fields(self, ticket_id: str, fields: dict[str, Any]) -> Ticket | None:
        if ticket_id != self.ticket.ticket_id:
            return None
        for key, value in fields.items():
            if hasattr(self.ticket, key):
                setattr(self.ticket, key, value)
        return self.ticket


class FakeEmbeddingService:
    def __init__(self) -> None:
        self.calls = 0

    def update_ticket_embedding(self, ticket: Ticket) -> bool:
        self.calls += 1
        return True


def test_update_ticket_refreshes_embedding_when_semantic_field_changes() -> None:
    repo = FakeRepository()
    embeddings = FakeEmbeddingService()
    service = TicketIngestionService(repository=repo, embedding_service=embeddings)

    result = service.update_ticket(
        ticket_id="TCK-1",
        payload=TicketUpdateInput.from_partial({"titulo": "Nuevo titulo"}),
        auto_embed=True,
    )

    assert result is not None
    assert result.embedding_refreshed is True
    assert embeddings.calls == 1


def test_update_ticket_skips_embedding_for_non_semantic_fields() -> None:
    repo = FakeRepository()
    embeddings = FakeEmbeddingService()
    service = TicketIngestionService(repository=repo, embedding_service=embeddings)

    result = service.update_ticket(
        ticket_id="TCK-1",
        payload=TicketUpdateInput.from_partial({"estado": "cerrado"}),
        auto_embed=True,
    )

    assert result is not None
    assert result.embedding_refreshed is False
    assert embeddings.calls == 0
