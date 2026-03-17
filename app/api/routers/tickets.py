from __future__ import annotations

from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import (
    get_response_builder,
    get_ticket_repository,
    get_ticket_search_service,
)
from app.application.services.response_builder import ResponseBuilder
from app.application.services.ticket_search_service import TicketSearchService
from app.infrastructure.config.settings import get_settings
from app.infrastructure.db.repositories.sqlalchemy_ticket_repository import (
    SqlAlchemyTicketRepository,
)
from app.schemas.search import TicketSearchResponse
from app.schemas.ticket import TicketResponse

router = APIRouter(prefix="/tickets", tags=["tickets"])
settings = get_settings()


@router.get("", response_model=list[TicketResponse])
def list_tickets(
    repository: Annotated[SqlAlchemyTicketRepository, Depends(get_ticket_repository)],
    limit: int = Query(default=20, ge=1, le=settings.max_query_limit),
    offset: int = Query(default=0, ge=0),
) -> list[TicketResponse]:
    tickets = repository.list_tickets(limit=limit, offset=offset)
    return [TicketResponse.model_validate(ticket) for ticket in tickets]


@router.get("/search", response_model=TicketSearchResponse)
def search_tickets(
    search_service: Annotated[TicketSearchService, Depends(get_ticket_search_service)],
    response_builder: Annotated[ResponseBuilder, Depends(get_response_builder)],
    query: str = Query(min_length=3),
    limit: int = Query(default=10, ge=1, le=settings.max_query_limit),
) -> TicketSearchResponse:
    ranked_tickets = search_service.search(query_text=query, limit=limit)
    response_text = response_builder.build_internal_support_response(
        query_text=query,
        ranked_tickets=ranked_tickets,
    )

    return TicketSearchResponse(
        query=query,
        response=response_text,
        results_count=len(ranked_tickets),
        results=[
            TicketResponse.model_validate(
                {
                    **asdict(ticket.ticket),
                    "relevance_score": round(ticket.relevance_score, 4),
                }
            )
            for ticket in ranked_tickets
        ],
    )
