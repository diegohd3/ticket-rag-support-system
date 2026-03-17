from __future__ import annotations

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.application.services.query_analyzer import QueryAnalyzer
from app.application.services.response_builder import ResponseBuilder
from app.application.services.ticket_search_service import TicketSearchService
from app.infrastructure.config.settings import get_settings
from app.infrastructure.db.repositories.sqlalchemy_ticket_repository import (
    SqlAlchemyTicketRepository,
)
from app.infrastructure.db.session import get_db_session


def get_db() -> Generator[Session, None, None]:
    yield from get_db_session()


def get_ticket_repository(
    db: Annotated[Session, Depends(get_db)],
) -> SqlAlchemyTicketRepository:
    return SqlAlchemyTicketRepository(db)


def get_query_analyzer() -> QueryAnalyzer:
    return QueryAnalyzer()


def get_ticket_search_service(
    repository: Annotated[SqlAlchemyTicketRepository, Depends(get_ticket_repository)],
    analyzer: Annotated[QueryAnalyzer, Depends(get_query_analyzer)],
) -> TicketSearchService:
    settings = get_settings()
    return TicketSearchService(
        repository=repository,
        analyzer=analyzer,
        candidate_limit=settings.search_candidate_limit,
    )


def get_response_builder() -> ResponseBuilder:
    return ResponseBuilder()
