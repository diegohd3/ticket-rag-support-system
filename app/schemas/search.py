from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.ticket import TicketResponse


class TicketSearchResponse(BaseModel):
    query: str
    strategy: str = "hybrid"
    applied_filters: dict[str, str] = Field(default_factory=dict)
    response: str
    results_count: int
    results: list[TicketResponse]
