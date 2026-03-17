from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.application.interfaces.embedding_provider import EmbeddingProvider
from app.application.interfaces.ticket_repository import TicketRepository
from app.application.services.ticket_embedding_service import TicketEmbeddingService
from app.domain.entities.ticket import Ticket
from app.domain.value_objects.search_filters import SearchFilters
from app.domain.value_objects.search_query import SearchQuery


def _ticket(ticket_id: str) -> Ticket:
    return Ticket(
        ticket_id=ticket_id,
        titulo=f"Titulo {ticket_id}",
        descripcion_problema="Problema de prueba",
        descripcion_solucion="Solucion de prueba",
        categoria="backend",
        prioridad="media",
        estado="cerrado",
        fecha_creacion=datetime.now(UTC),
        fecha_cierre=None,
        tags=["test"],
        usuario_creador="qa",
        sistema_afectado="api",
        logs={},
        causa_raiz=None,
        pasos_diagnostico=None,
        entorno="test",
        version_sistema="1.0.0",
        impacto="low",
        resuelto_exitosamente=True,
    )


class FakeEmbeddingProvider(EmbeddingProvider):
    def is_available(self) -> bool:
        return True

    def embed_text(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]


class FakeTicketRepository(TicketRepository):
    def __init__(self) -> None:
        self.missing = [_ticket("TCK-1"), _ticket("TCK-2")]
        self.stale = [_ticket("TCK-3")]
        self.update_calls: list[tuple[str, str]] = []

    def count_tickets(self) -> int:
        return len(self.missing) + len(self.stale)

    def list_tickets(self, limit: int, offset: int) -> list[Ticket]:
        all_rows = self.missing + self.stale
        return all_rows[offset : offset + limit]

    def get_ticket_by_ticket_id(self, ticket_id: str) -> Ticket | None:
        for ticket in self.missing + self.stale:
            if ticket.ticket_id == ticket_id:
                return ticket
        return None

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
        return self.missing[offset : offset + limit]

    def list_tickets_with_stale_embeddings(
        self,
        limit: int,
        embedding_model: str,
        offset: int = 0,
    ) -> list[Ticket]:
        return self.stale[offset : offset + limit]

    def update_ticket_embedding(
        self,
        ticket_id: str,
        embedding: list[float],
        embedding_model: str,
    ) -> bool:
        self.update_calls.append((ticket_id, embedding_model))
        return True

    def create_ticket(self, ticket: Ticket) -> Ticket:
        return ticket

    def update_ticket_fields(self, ticket_id: str, fields: dict[str, Any]) -> Ticket | None:
        ticket = self.get_ticket_by_ticket_id(ticket_id)
        if not ticket:
            return None
        for field_name, value in fields.items():
            if hasattr(ticket, field_name):
                setattr(ticket, field_name, value)
        return ticket


def test_reindex_missing_mode_processes_batches() -> None:
    repository = FakeTicketRepository()
    service = TicketEmbeddingService(
        repository=repository,
        embedding_provider=FakeEmbeddingProvider(),
        embedding_model="text-embedding-3-small",
        batch_size=1,
    )

    result = service.reindex_embeddings(limit=2, mode="missing")

    assert result.mode == "missing"
    assert result.processed == 2
    assert result.updated == 2
    assert result.failed == 0
    assert repository.update_calls == [
        ("TCK-1", "text-embedding-3-small"),
        ("TCK-2", "text-embedding-3-small"),
    ]


def test_reindex_stale_mode_uses_stale_selector() -> None:
    repository = FakeTicketRepository()
    service = TicketEmbeddingService(
        repository=repository,
        embedding_provider=FakeEmbeddingProvider(),
        embedding_model="text-embedding-3-small",
    )

    result = service.reindex_embeddings(limit=10, mode="stale")

    assert result.mode == "stale"
    assert result.processed == 1
    assert result.updated == 1
    assert repository.update_calls == [("TCK-3", "text-embedding-3-small")]
