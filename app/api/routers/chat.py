from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_support_assistant_service
from app.application.services.support_assistant_service import SupportAssistantService
from app.schemas.chat import ChatAskRequest, ChatAskResponse, ChatSource

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/ask", response_model=ChatAskResponse)
def ask_support(
    payload: ChatAskRequest,
    assistant: Annotated[SupportAssistantService, Depends(get_support_assistant_service)],
) -> ChatAskResponse:
    result = assistant.ask(query_text=payload.query, top_k=payload.top_k)
    return ChatAskResponse(
        query=result.query,
        answer=result.answer,
        used_llm=result.used_llm,
        results_count=len(result.ranked_tickets),
        sources=[
            ChatSource(
                ticket_id=entry.ticket.ticket_id,
                titulo=entry.ticket.titulo,
                categoria=entry.ticket.categoria,
                prioridad=entry.ticket.prioridad,
                relevance_score=round(entry.relevance_score, 4),
                text_score=round(entry.text_score, 4),
                semantic_score=round(entry.semantic_score, 4),
            )
            for entry in result.ranked_tickets
        ],
    )
