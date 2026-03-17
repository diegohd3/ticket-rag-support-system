from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Literal

from app.application.interfaces.embedding_provider import EmbeddingProvider
from app.application.interfaces.ticket_repository import TicketRepository
from app.application.services.ticket_search_service import TicketSearchService
from app.domain.entities.ticket import Ticket

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class EmbeddingReindexResult:
    mode: str
    processed: int
    updated: int
    failed: int
    failures: list[str]


class TicketEmbeddingService:
    def __init__(
        self,
        repository: TicketRepository,
        embedding_provider: EmbeddingProvider,
        embedding_model: str,
        batch_size: int = 50,
    ) -> None:
        self._repository = repository
        self._embedding_provider = embedding_provider
        self._embedding_model = embedding_model
        self._batch_size = max(1, batch_size)

    def update_ticket_embedding(self, ticket: Ticket) -> bool:
        if not self._embedding_provider.is_available():
            logger.info(
                "Embedding provider is not available. Skipping embedding for ticket_id=%s",
                ticket.ticket_id,
            )
            return False

        embedding_input = TicketSearchService.build_embedding_input(ticket)
        embedding = self._embedding_provider.embed_text(embedding_input)
        return self._repository.update_ticket_embedding(
            ticket_id=ticket.ticket_id,
            embedding=embedding,
            embedding_model=self._embedding_model,
        )

    def reindex_embeddings(
        self,
        limit: int,
        mode: Literal["missing", "stale", "all"] = "missing",
    ) -> EmbeddingReindexResult:
        processed = 0
        updated = 0
        failed = 0
        failures: list[str] = []
        offset = 0
        remaining = max(0, limit)

        while remaining > 0:
            batch_limit = min(self._batch_size, remaining)
            tickets = self._load_batch(mode=mode, limit=batch_limit, offset=offset)
            if not tickets:
                break

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

            offset += len(tickets)
            remaining -= len(tickets)

        return EmbeddingReindexResult(
            mode=mode,
            processed=processed,
            updated=updated,
            failed=failed,
            failures=failures[:20],
        )

    def _load_batch(
        self,
        mode: Literal["missing", "stale", "all"],
        limit: int,
        offset: int,
    ) -> list[Ticket]:
        if mode == "all":
            return self._repository.list_tickets(limit=limit, offset=offset)
        if mode == "stale":
            return self._repository.list_tickets_with_stale_embeddings(
                limit=limit,
                offset=offset,
                embedding_model=self._embedding_model,
            )
        return self._repository.list_tickets_without_embeddings(limit=limit, offset=offset)
