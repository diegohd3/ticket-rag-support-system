from __future__ import annotations

import logging
from dataclasses import dataclass

from app.application.interfaces.support_answer_provider import SupportAnswerProvider
from app.application.services.response_builder import ResponseBuilder
from app.application.services.ticket_search_service import RankedTicket, TicketSearchService

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class SupportAnswerResult:
    query: str
    answer: str
    ranked_tickets: list[RankedTicket]
    used_llm: bool


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

    def ask(self, query_text: str, top_k: int) -> SupportAnswerResult:
        ranked_tickets = self._ticket_search_service.search(query_text=query_text, limit=top_k)

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
        )
