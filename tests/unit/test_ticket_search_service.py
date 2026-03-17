from __future__ import annotations

from datetime import UTC, datetime

from app.application.interfaces.embedding_provider import EmbeddingProvider
from app.application.interfaces.ticket_repository import TicketRepository
from app.application.services.query_analyzer import QueryAnalyzer
from app.application.services.ticket_search_service import TicketSearchService
from app.domain.entities.ticket import Ticket
from app.domain.value_objects.search_query import SearchQuery


def _ticket(ticket_id: str, titulo: str, problema: str, tags: list[str]) -> Ticket:
    return Ticket(
        ticket_id=ticket_id,
        titulo=titulo,
        descripcion_problema=problema,
        descripcion_solucion="restart service",
        categoria="backend",
        prioridad="media",
        estado="cerrado",
        fecha_creacion=datetime.now(UTC),
        fecha_cierre=None,
        tags=tags,
        usuario_creador="tester",
        sistema_afectado="api",
        logs={"trace": "abc"},
        causa_raiz=None,
        pasos_diagnostico=None,
        entorno="dev",
        version_sistema="1.0.0",
        impacto="low",
        resuelto_exitosamente=True,
    )


class FakeEmbeddingProvider(EmbeddingProvider):
    def embed_text(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]

    def is_available(self) -> bool:
        return True


class FakeRepository(TicketRepository):
    def __init__(self) -> None:
        self.t1 = _ticket("TCK-1", "ERR-401 login failure", "Error ERR-401 at login", ["auth"])
        self.t2 = _ticket("TCK-2", "Cache issue", "Intermittent failure", ["cache"])

    def list_tickets(self, limit: int, offset: int) -> list[Ticket]:
        return [self.t1, self.t2][offset : offset + limit]

    def search_candidates(self, query: SearchQuery, limit: int) -> list[Ticket]:
        return [self.t1, self.t2][:limit]

    def semantic_search(
        self,
        query_embedding: list[float],
        limit: int,
    ) -> list[tuple[Ticket, float]]:
        return [(self.t2, 0.9), (self.t1, 0.2)][:limit]

    def list_tickets_without_embeddings(self, limit: int) -> list[Ticket]:
        return [self.t1][:limit]

    def update_ticket_embedding(self, ticket_id: str, embedding: list[float]) -> bool:
        return True

    def create_ticket(self, ticket: Ticket) -> Ticket:
        return ticket


def test_hybrid_search_combines_text_and_semantic_scores() -> None:
    repository = FakeRepository()
    service = TicketSearchService(
        repository=repository,
        analyzer=QueryAnalyzer(),
        embedding_provider=FakeEmbeddingProvider(),
        text_weight=0.1,
        semantic_weight=0.9,
    )

    results = service.search(query_text="ERR-401 on login", limit=2)

    assert len(results) == 2
    # Ticket 2 ranks first due to strong semantic similarity
    assert results[0].ticket.ticket_id == "TCK-2"
    assert results[0].semantic_score > results[1].semantic_score
