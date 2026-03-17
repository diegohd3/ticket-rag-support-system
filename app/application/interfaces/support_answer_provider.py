from __future__ import annotations

from abc import ABC, abstractmethod

from app.application.services.ticket_search_service import RankedTicket


class SupportAnswerProvider(ABC):
    @abstractmethod
    def is_available(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def generate_support_answer(self, query_text: str, ranked_tickets: list[RankedTicket]) -> str:
        raise NotImplementedError
