from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_support_assistant_service, require_api_key
from app.application.services.support_assistant_service import SupportAssistantService
from app.domain.value_objects.search_filters import SearchFilters
from app.schemas.chat import ChatAskRequest, ChatAskResponse, ChatSource

router = APIRouter(prefix="/chat", tags=["chat"], dependencies=[Depends(require_api_key)])


@router.post("/ask", response_model=ChatAskResponse)
def ask_support(
    payload: ChatAskRequest,
    assistant: Annotated[SupportAssistantService, Depends(get_support_assistant_service)],
) -> ChatAskResponse:
    filters = SearchFilters(
        categoria=payload.categoria,
        prioridad=payload.prioridad,
        estado=payload.estado,
        sistema_afectado=payload.sistema_afectado,
    )
    filters_or_none = (
        None
        if not any([filters.categoria, filters.prioridad, filters.estado, filters.sistema_afectado])
        else filters
    )
    result = assistant.ask(query_text=payload.query, top_k=payload.top_k, filters=filters_or_none)

    applied_filters = {
        key: value
        for key, value in {
            "categoria": payload.categoria,
            "prioridad": payload.prioridad,
            "estado": payload.estado,
            "sistema_afectado": payload.sistema_afectado,
        }.items()
        if value
    }
    return ChatAskResponse(
        query=result.query,
        applied_filters=applied_filters,
        answer=result.answer,
        used_llm=result.used_llm,
        confidence=result.confidence,
        evidence_ticket_ids=result.evidence_ticket_ids,
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
                rerank_score=(
                    round(entry.rerank_score, 4) if entry.rerank_score is not None else None
                ),
            )
            for entry in result.ranked_tickets
        ],
    )
