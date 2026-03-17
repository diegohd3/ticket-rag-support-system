from __future__ import annotations

from pydantic import BaseModel

from app.schemas.ticket import TicketResponse


class TicketSearchResponse(BaseModel):
    query: str
    response: str
    results_count: int
    results: list[TicketResponse]
