from __future__ import annotations

from pydantic import BaseModel, Field


class ChatAskRequest(BaseModel):
    query: str = Field(min_length=3, description="Technical issue described in natural language.")
    top_k: int = Field(default=5, ge=1, le=20)


class ChatSource(BaseModel):
    ticket_id: str
    titulo: str
    categoria: str
    prioridad: str
    relevance_score: float
    text_score: float
    semantic_score: float


class ChatAskResponse(BaseModel):
    query: str
    answer: str
    used_llm: bool
    results_count: int
    sources: list[ChatSource]
