from __future__ import annotations

import argparse
from typing import Literal

from app.application.services.ticket_embedding_service import TicketEmbeddingService
from app.infrastructure.ai.openai_embedding_provider import OpenAIEmbeddingProvider
from app.infrastructure.config.settings import get_settings
from app.infrastructure.db.repositories.sqlalchemy_ticket_repository import (
    SqlAlchemyTicketRepository,
)
from app.infrastructure.db.session import SessionLocal


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reindex ticket embeddings in PostgreSQL.")
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Max tickets to process in this run.",
    )
    parser.add_argument(
        "--mode",
        choices=["missing", "stale", "all"],
        default="missing",
        help="Reindex mode: missing vectors, stale vectors, or all tickets.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=0,
        help="Optional per-batch size. 0 uses EMBEDDING_REINDEX_BATCH_SIZE.",
    )
    return parser.parse_args()


def run_reindex(
    limit: int,
    mode: Literal["missing", "stale", "all"],
    batch_size: int = 0,
) -> None:
    settings = get_settings()
    embedding_provider = OpenAIEmbeddingProvider(settings=settings)
    effective_batch_size = batch_size if batch_size > 0 else settings.embedding_reindex_batch_size

    with SessionLocal() as session:
        repository = SqlAlchemyTicketRepository(
            session,
            vector_probes=settings.vector_search_probes,
        )
        service = TicketEmbeddingService(
            repository=repository,
            embedding_provider=embedding_provider,
            embedding_model=settings.embedding_model,
            batch_size=effective_batch_size,
        )
        result = service.reindex_embeddings(limit=limit, mode=mode)

    print(
        "Embedding reindex completed: "
        f"mode={result.mode} processed={result.processed} "
        f"updated={result.updated} failed={result.failed}"
    )
    if result.failures:
        print("Failures:")
        for failure in result.failures:
            print(f" - {failure}")


if __name__ == "__main__":
    args = parse_args()
    run_reindex(limit=args.limit, mode=args.mode, batch_size=args.batch_size)
