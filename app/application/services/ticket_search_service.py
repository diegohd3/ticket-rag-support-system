from __future__ import annotations

import logging
from dataclasses import dataclass

from app.application.interfaces.embedding_provider import EmbeddingProvider
from app.application.interfaces.ticket_repository import TicketRepository
from app.application.services.query_analyzer import QueryAnalyzer
from app.domain.entities.ticket import Ticket
from app.domain.value_objects.search_query import SearchQuery

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RankedTicket:
    ticket: Ticket
    relevance_score: float
    text_score: float = 0.0
    semantic_score: float = 0.0


class TicketSearchService:
    def __init__(
        self,
        repository: TicketRepository,
        analyzer: QueryAnalyzer,
        embedding_provider: EmbeddingProvider | None = None,
        candidate_limit: int = 50,
        semantic_candidate_limit: int = 25,
        semantic_search_enabled: bool = True,
        text_weight: float = 0.55,
        semantic_weight: float = 0.45,
    ) -> None:
        self._repository = repository
        self._analyzer = analyzer
        self._embedding_provider = embedding_provider
        self._candidate_limit = candidate_limit
        self._semantic_candidate_limit = semantic_candidate_limit
        self._semantic_search_enabled = semantic_search_enabled
        self._text_weight = text_weight
        self._semantic_weight = semantic_weight

    def search(self, query_text: str, limit: int) -> list[RankedTicket]:
        analyzed_query = self._analyzer.analyze(query_text)
        candidate_count = max(limit, min(self._candidate_limit, max(limit * 3, 15)))
        text_candidates = self._repository.search_candidates(analyzed_query, limit=candidate_count)
        text_ranked = self._rank_text_candidates(text_candidates, analyzed_query)
        text_score_map = {entry.ticket.ticket_id: entry.text_score for entry in text_ranked}

        semantic_score_map: dict[str, float] = {}
        semantic_ticket_map: dict[str, Ticket] = {}
        if self._should_run_semantic_search():
            semantic_score_map, semantic_ticket_map = self._run_semantic_search(
                query_text=query_text,
                limit=limit,
            )

        merged: dict[str, RankedTicket] = {}

        for entry in text_ranked:
            merged[entry.ticket.ticket_id] = RankedTicket(
                ticket=entry.ticket,
                relevance_score=0.0,
                text_score=entry.text_score,
                semantic_score=semantic_score_map.get(entry.ticket.ticket_id, 0.0),
            )

        for ticket_id, semantic_score in semantic_score_map.items():
            if ticket_id in merged:
                continue
            ticket = semantic_ticket_map[ticket_id]
            merged[ticket_id] = RankedTicket(
                ticket=ticket,
                relevance_score=0.0,
                text_score=text_score_map.get(ticket_id, 0.0),
                semantic_score=semantic_score,
            )

        for entry in merged.values():
            entry.relevance_score = (
                self._text_weight * entry.text_score + self._semantic_weight * entry.semantic_score
            )

        ranked = sorted(merged.values(), key=lambda item: item.relevance_score, reverse=True)
        return ranked[:limit]

    def _should_run_semantic_search(self) -> bool:
        return (
            self._semantic_search_enabled
            and self._embedding_provider is not None
            and self._embedding_provider.is_available()
        )

    def _run_semantic_search(
        self,
        query_text: str,
        limit: int,
    ) -> tuple[dict[str, float], dict[str, Ticket]]:
        try:
            query_embedding = self._embedding_provider.embed_text(query_text)  # type: ignore[union-attr]
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Semantic search disabled for this query due to embedding error: %s",
                exc,
            )
            return {}, {}

        semantic_limit = max(limit, self._semantic_candidate_limit)
        semantic_matches = self._repository.semantic_search(
            query_embedding=query_embedding,
            limit=semantic_limit,
        )

        semantic_score_map: dict[str, float] = {}
        semantic_ticket_map: dict[str, Ticket] = {}
        for ticket, raw_similarity in semantic_matches:
            # cosine similarity may be in [-1, 1]; normalize to [0, 1]
            normalized_score = max(0.0, min(1.0, (raw_similarity + 1.0) / 2.0))
            semantic_score_map[ticket.ticket_id] = normalized_score
            semantic_ticket_map[ticket.ticket_id] = ticket

        return semantic_score_map, semantic_ticket_map

    def _rank_text_candidates(
        self,
        tickets: list[Ticket],
        query: SearchQuery,
    ) -> list[RankedTicket]:
        raw_scores = [self._score_ticket(ticket, query) for ticket in tickets]
        max_score = max(raw_scores, default=0.0)
        if max_score <= 0:
            max_score = 1.0

        ranked = [
            RankedTicket(
                ticket=ticket,
                relevance_score=0.0,
                text_score=raw_score / max_score,
                semantic_score=0.0,
            )
            for ticket, raw_score in zip(tickets, raw_scores, strict=False)
        ]
        ranked.sort(key=lambda item: item.text_score, reverse=True)
        return ranked

    def _score_ticket(self, ticket: Ticket, query: SearchQuery) -> float:
        ticket_text = self._build_ticket_text(ticket)
        title_text = ticket.titulo.lower()

        keyword_hits = sum(1 for keyword in query.keywords if keyword in ticket_text)
        error_code_hits = sum(1 for code in query.error_codes if code.lower() in ticket_text)
        tag_hits = sum(1 for tag in query.tags if tag.lower() in {t.lower() for t in ticket.tags})

        exact_phrase_bonus = (
            2.0 if query.normalized_text and query.normalized_text in ticket_text else 0.0
        )
        title_match_bonus = (
            1.5 if query.normalized_text and query.normalized_text in title_text else 0.0
        )
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
    def build_embedding_input(ticket: Ticket) -> str:
        chunks = [
            f"Ticket ID: {ticket.ticket_id}",
            f"Titulo: {ticket.titulo}",
            f"Problema: {ticket.descripcion_problema}",
            f"Solucion: {ticket.descripcion_solucion}",
            f"Categoria: {ticket.categoria}",
            f"Sistema afectado: {ticket.sistema_afectado}",
            f"Tags: {', '.join(ticket.tags)}",
            f"Causa raiz: {ticket.causa_raiz or ''}",
            f"Pasos de diagnostico: {ticket.pasos_diagnostico or ''}",
            f"Logs: {ticket.logs}",
        ]
        return "\n".join(chunks)

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
