from __future__ import annotations

from pydantic import BaseModel, Field


class ChatAskRequest(BaseModel):
    query: str = Field(min_length=3, description="Technical issue described in natural language.")
    top_k: int = Field(default=5, ge=1, le=20)
    categoria: str | None = None
    prioridad: str | None = None
    estado: str | None = None
    sistema_afectado: str | None = None


class ChatSource(BaseModel):
    ticket_id: str
    titulo: str
    categoria: str
    prioridad: str
    relevance_score: float
    text_score: float
    semantic_score: float
    rerank_score: float | None = None


class ChatAskResponse(BaseModel):
    query: str
    applied_filters: dict[str, str] = Field(default_factory=dict)
    answer: str
    used_llm: bool
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_ticket_ids: list[str] = Field(default_factory=list)
    results_count: int
    sources: list[ChatSource]
