from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.ticket import Ticket
from app.domain.value_objects.search_filters import SearchFilters
from app.domain.value_objects.search_query import SearchQuery


class TicketRepository(ABC):
    @abstractmethod
    def list_tickets(self, limit: int, offset: int) -> list[Ticket]:
        raise NotImplementedError

    @abstractmethod
    def search_candidates(self, query: SearchQuery, limit: int) -> list[Ticket]:
        raise NotImplementedError

    @abstractmethod
    def semantic_search(
        self,
        query_embedding: list[float],
        limit: int,
        filters: SearchFilters | None = None,
    ) -> list[tuple[Ticket, float]]:
        """Returns (ticket, similarity_score) where higher is better."""
        raise NotImplementedError

    @abstractmethod
    def list_tickets_without_embeddings(self, limit: int, offset: int = 0) -> list[Ticket]:
        raise NotImplementedError

    @abstractmethod
    def list_tickets_with_stale_embeddings(
        self,
        limit: int,
        embedding_model: str,
        offset: int = 0,
    ) -> list[Ticket]:
        raise NotImplementedError

    @abstractmethod
    def update_ticket_embedding(
        self,
        ticket_id: str,
        embedding: list[float],
        embedding_model: str,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    def create_ticket(self, ticket: Ticket) -> Ticket:
        raise NotImplementedError
