from __future__ import annotations

import argparse

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
        "--only-missing",
        action="store_true",
        help="Only process tickets without embeddings.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all tickets up to limit.",
    )
    return parser.parse_args()


def run_reindex(limit: int, only_missing: bool) -> None:
    settings = get_settings()
    embedding_provider = OpenAIEmbeddingProvider(settings=settings)

    with SessionLocal() as session:
        repository = SqlAlchemyTicketRepository(session)
        service = TicketEmbeddingService(
            repository=repository,
            embedding_provider=embedding_provider,
        )
        result = service.reindex_embeddings(limit=limit, only_missing=only_missing)

    print(
        "Embedding reindex completed: "
        f"processed={result.processed} updated={result.updated} failed={result.failed}"
    )
    if result.failures:
        print("Failures:")
        for failure in result.failures:
            print(f" - {failure}")


if __name__ == "__main__":
    args = parse_args()
    only_missing_flag = False if args.all else True
    if args.only_missing:
        only_missing_flag = True
    run_reindex(limit=args.limit, only_missing=only_missing_flag)
