from __future__ import annotations

import logging
from dataclasses import dataclass

from app.application.interfaces.support_answer_provider import SupportAnswerProvider
from app.application.services.response_builder import ResponseBuilder
from app.application.services.ticket_search_service import RankedTicket, TicketSearchService
from app.domain.value_objects.search_filters import SearchFilters

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class SupportAnswerResult:
    query: str
    answer: str
    ranked_tickets: list[RankedTicket]
    used_llm: bool
    confidence: float
    evidence_ticket_ids: list[str]


class SupportAssistantService:
    def __init__(
        self,
        ticket_search_service: TicketSearchService,
        response_builder: ResponseBuilder,
        answer_provider: SupportAnswerProvider | None = None,
    ) -> None:
        self._ticket_search_service = ticket_search_service
        self._response_builder = response_builder
        self._answer_provider = answer_provider

    def ask(
        self,
        query_text: str,
        top_k: int,
        filters: SearchFilters | None = None,
    ) -> SupportAnswerResult:
        ranked_tickets = self._ticket_search_service.search(
            query_text=query_text,
            limit=top_k,
            filters=filters,
        )
        confidence = self._compute_confidence(ranked_tickets)
        evidence_ticket_ids = [entry.ticket.ticket_id for entry in ranked_tickets[:3]]

        if not ranked_tickets:
            fallback_answer = self._response_builder.build_internal_support_response(
                query_text=query_text,
                ranked_tickets=[],
            )
            return SupportAnswerResult(
                query=query_text,
                answer=fallback_answer,
                ranked_tickets=[],
                used_llm=False,
                confidence=0.0,
                evidence_ticket_ids=[],
            )

        if self._answer_provider and self._answer_provider.is_available():
            try:
                answer = self._answer_provider.generate_support_answer(
                    query_text=query_text,
                    ranked_tickets=ranked_tickets,
                )
                return SupportAnswerResult(
                    query=query_text,
                    answer=answer,
                    ranked_tickets=ranked_tickets,
                    used_llm=True,
                    confidence=confidence,
                    evidence_ticket_ids=evidence_ticket_ids,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Falling back to internal deterministic response due to LLM error: %s",
                    exc,
                )

        fallback_answer = self._response_builder.build_internal_support_response(
            query_text=query_text,
            ranked_tickets=ranked_tickets,
        )
        return SupportAnswerResult(
            query=query_text,
            answer=fallback_answer,
            ranked_tickets=ranked_tickets,
            used_llm=False,
            confidence=confidence,
            evidence_ticket_ids=evidence_ticket_ids,
        )

    @staticmethod
    def _compute_confidence(ranked_tickets: list[RankedTicket]) -> float:
        if not ranked_tickets:
            return 0.0

        top = max(0.0, min(1.0, ranked_tickets[0].relevance_score))
        second = (
            max(0.0, min(1.0, ranked_tickets[1].relevance_score))
            if len(ranked_tickets) > 1
            else 0.0
        )
        margin = max(0.0, top - second)
        evidence_window = ranked_tickets[:3]
        resolved_ratio = sum(
            1.0 for item in evidence_window if item.ticket.resuelto_exitosamente
        ) / len(evidence_window)

        confidence = (0.65 * top) + (0.2 * margin) + (0.15 * resolved_ratio)
        return round(max(0.0, min(1.0, confidence)), 4)
