from __future__ import annotations

from dataclasses import dataclass

from app.application.interfaces.ticket_repository import TicketRepository
from app.application.services.query_analyzer import QueryAnalyzer
from app.domain.entities.ticket import Ticket
from app.domain.value_objects.search_query import SearchQuery


@dataclass(slots=True)
class RankedTicket:
    ticket: Ticket
    relevance_score: float


class TicketSearchService:
    def __init__(
        self,
        repository: TicketRepository,
        analyzer: QueryAnalyzer,
        candidate_limit: int = 50,
    ) -> None:
        self._repository = repository
        self._analyzer = analyzer
        self._candidate_limit = candidate_limit

    def search(self, query_text: str, limit: int) -> list[RankedTicket]:
        analyzed_query = self._analyzer.analyze(query_text)
        candidate_count = max(limit, min(self._candidate_limit, max(limit * 3, 15)))
        candidates = self._repository.search_candidates(analyzed_query, limit=candidate_count)
        ranked = [RankedTicket(ticket=t, relevance_score=self._score_ticket(t, analyzed_query)) for t in candidates]
        ranked.sort(key=lambda item: item.relevance_score, reverse=True)
        return ranked[:limit]

    def _score_ticket(self, ticket: Ticket, query: SearchQuery) -> float:
        ticket_text = self._build_ticket_text(ticket)
        title_text = ticket.titulo.lower()

        keyword_hits = sum(1 for keyword in query.keywords if keyword in ticket_text)
        error_code_hits = sum(1 for code in query.error_codes if code.lower() in ticket_text)
        tag_hits = sum(1 for tag in query.tags if tag.lower() in {t.lower() for t in ticket.tags})

        exact_phrase_bonus = 2.0 if query.normalized_text and query.normalized_text in ticket_text else 0.0
        title_match_bonus = 1.5 if query.normalized_text and query.normalized_text in title_text else 0.0
        resolution_bonus = 0.5 if ticket.resuelto_exitosamente else 0.0

        return (
            keyword_hits * 1.0
            + error_code_hits * 2.5
            + tag_hits * 2.0
            + exact_phrase_bonus
            + title_match_bonus
            + resolution_bonus
        )

    @staticmethod
    def _build_ticket_text(ticket: Ticket) -> str:
        chunks = [
            ticket.titulo,
            ticket.descripcion_problema,
            ticket.descripcion_solucion,
            ticket.categoria,
            ticket.sistema_afectado,
            ticket.causa_raiz or "",
            ticket.pasos_diagnostico or "",
            ticket.entorno or "",
            ticket.version_sistema or "",
            ticket.impacto or "",
            " ".join(ticket.tags),
            str(ticket.logs),
        ]
        return " ".join(chunks).lower()
