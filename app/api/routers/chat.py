from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import (
    ChatUserContext,
    get_support_assistant_service,
    get_user_guard_service,
    require_api_key,
    require_chat_user,
)
from app.application.services.support_assistant_service import SupportAssistantService
from app.application.services.user_guard_service import UserGuardService
from app.domain.value_objects.search_filters import SearchFilters
from app.schemas.chat import ChatAskRequest, ChatAskResponse, ChatSource

router = APIRouter(prefix="/chat", tags=["chat"], dependencies=[Depends(require_api_key)])


@router.post("/ask", response_model=ChatAskResponse)
def ask_support(
    payload: ChatAskRequest,
    assistant: Annotated[SupportAssistantService, Depends(get_support_assistant_service)],
    user_context: Annotated[ChatUserContext, Depends(require_chat_user)],
    user_guard: Annotated[UserGuardService, Depends(get_user_guard_service)],
) -> ChatAskResponse:
    guard_result = user_guard.evaluate_query(user_id=user_context.user_id, query_text=payload.query)
    if not guard_result.allowed:
        if guard_result.blocked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "user_blocked",
                    "message": "Account blocked due repeated non-technical or invalid queries.",
                },
            )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "unsupported_query",
                "message": (
                    "Query appears off-topic for technical support. "
                    "Repeated invalid attempts can block this account."
                ),
                "details": {
                    "violation_count": guard_result.violation_count,
                    "reason": guard_result.reason,
                },
            },
        )

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
