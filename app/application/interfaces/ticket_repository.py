from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.ticket import Ticket
from app.domain.value_objects.search_query import SearchQuery


class TicketRepository(ABC):
    @abstractmethod
    def list_tickets(self, limit: int, offset: int) -> list[Ticket]:
        raise NotImplementedError

    @abstractmethod
    def search_candidates(self, query: SearchQuery, limit: int) -> list[Ticket]:
        raise NotImplementedError
