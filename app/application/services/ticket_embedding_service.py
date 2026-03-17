from __future__ import annotations

import logging
from dataclasses import dataclass

from app.application.interfaces.embedding_provider import EmbeddingProvider
from app.application.interfaces.ticket_repository import TicketRepository
from app.application.services.ticket_search_service import TicketSearchService
from app.domain.entities.ticket import Ticket

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class EmbeddingReindexResult:
    processed: int
    updated: int
    failed: int
    failures: list[str]


class TicketEmbeddingService:
    def __init__(
        self,
        repository: TicketRepository,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self._repository = repository
        self._embedding_provider = embedding_provider

    def update_ticket_embedding(self, ticket: Ticket) -> bool:
        if not self._embedding_provider.is_available():
            logger.info(
                "Embedding provider is not available. Skipping embedding for ticket_id=%s",
                ticket.ticket_id,
            )
            return False

        embedding_input = TicketSearchService.build_embedding_input(ticket)
        embedding = self._embedding_provider.embed_text(embedding_input)
        return self._repository.update_ticket_embedding(ticket.ticket_id, embedding)

    def reindex_embeddings(self, limit: int, only_missing: bool) -> EmbeddingReindexResult:
        if only_missing:
            tickets = self._repository.list_tickets_without_embeddings(limit=limit)
        else:
            tickets = self._repository.list_tickets(limit=limit, offset=0)

        processed = 0
        updated = 0
        failed = 0
        failures: list[str] = []

        for ticket in tickets:
            processed += 1
            try:
                result = self.update_ticket_embedding(ticket)
                if result:
                    updated += 1
                else:
                    failed += 1
                    failures.append(f"{ticket.ticket_id}: embedding update returned false")
            except Exception as exc:  # noqa: BLE001
                failed += 1
                failures.append(f"{ticket.ticket_id}: {exc}")
                logger.warning("Failed to embed ticket_id=%s error=%s", ticket.ticket_id, exc)

        return EmbeddingReindexResult(
            processed=processed,
            updated=updated,
            failed=failed,
            failures=failures[:20],
        )
