from __future__ import annotations

from dataclasses import asdict
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import (
    ChatUserContext,
    get_response_builder,
    get_ticket_embedding_service,
    get_ticket_ingestion_service,
    get_ticket_repository,
    get_ticket_search_service,
    require_admin_user,
    require_api_key,
    require_chat_user,
)
from app.api.search_filters import build_applied_filters, build_optional_search_filters
from app.application.services.response_builder import ResponseBuilder
from app.application.services.ticket_embedding_service import TicketEmbeddingService
from app.application.services.ticket_ingestion_service import (
    TicketCreateInput,
    TicketIngestionService,
    TicketUpdateInput,
)
from app.application.services.ticket_search_service import TicketSearchService
from app.infrastructure.config.settings import get_settings
from app.infrastructure.db.repositories.sqlalchemy_ticket_repository import (
    SqlAlchemyTicketRepository,
)
from app.schemas.search import TicketSearchResponse
from app.schemas.ticket import (
    EmbeddingReindexResponse,
    TicketCreateRequest,
    TicketCreateResponse,
    TicketListResponse,
    TicketResponse,
    TicketUpdateRequest,
    TicketUpdateResponse,
)

router = APIRouter(prefix="/tickets", tags=["tickets"], dependencies=[Depends(require_api_key)])
settings = get_settings()


@router.get("", response_model=TicketListResponse)
def list_tickets(
    repository: Annotated[SqlAlchemyTicketRepository, Depends(get_ticket_repository)],
    _user: Annotated[ChatUserContext, Depends(require_chat_user)],
    limit: int = Query(default=20, ge=1, le=settings.max_query_limit),
    offset: int = Query(default=0, ge=0),
) -> TicketListResponse:
    tickets = repository.list_tickets(limit=limit, offset=offset)
    total = repository.count_tickets()
    items = [TicketResponse.model_validate(ticket) for ticket in tickets]
    return TicketListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_next=offset + len(items) < total,
    )


@router.get("/search", response_model=TicketSearchResponse)
def search_tickets(
    search_service: Annotated[TicketSearchService, Depends(get_ticket_search_service)],
    response_builder: Annotated[ResponseBuilder, Depends(get_response_builder)],
    _user: Annotated[ChatUserContext, Depends(require_chat_user)],
    query: str = Query(min_length=3, max_length=1200),
    limit: int = Query(default=10, ge=1, le=settings.max_query_limit),
    categoria: str | None = Query(default=None),
    prioridad: str | None = Query(default=None),
    estado: str | None = Query(default=None),
    sistema_afectado: str | None = Query(default=None),
) -> TicketSearchResponse:
    filters = build_optional_search_filters(
        categoria=categoria,
        prioridad=prioridad,
        estado=estado,
        sistema_afectado=sistema_afectado,
    )
    ranked_tickets = search_service.search(query_text=query, limit=limit, filters=filters)
    response_text = response_builder.build_internal_support_response(
        query_text=query,
        ranked_tickets=ranked_tickets,
    )

    applied_filters = build_applied_filters(
        categoria=categoria,
        prioridad=prioridad,
        estado=estado,
        sistema_afectado=sistema_afectado,
    )

    return TicketSearchResponse(
        query=query,
        strategy="hybrid",
        applied_filters=applied_filters,
        response=response_text,
        results_count=len(ranked_tickets),
        results=[
            TicketResponse.model_validate(
                {
                    **asdict(ticket.ticket),
                    "relevance_score": round(ticket.relevance_score, 4),
                    "text_score": round(ticket.text_score, 4),
                    "semantic_score": round(ticket.semantic_score, 4),
                    "rerank_score": (
                        round(ticket.rerank_score, 4) if ticket.rerank_score is not None else None
                    ),
                }
            )
            for ticket in ranked_tickets
        ],
    )


@router.post("", response_model=TicketCreateResponse)
def create_ticket(
    payload: TicketCreateRequest,
    ingestion_service: Annotated[TicketIngestionService, Depends(get_ticket_ingestion_service)],
    _admin: Annotated[ChatUserContext, Depends(require_admin_user)],
) -> TicketCreateResponse:
    result = ingestion_service.create_ticket(
        payload=TicketCreateInput(
            ticket_id=payload.ticket_id,
            titulo=payload.titulo,
            descripcion_problema=payload.descripcion_problema,
            descripcion_solucion=payload.descripcion_solucion,
            categoria=payload.categoria,
            prioridad=payload.prioridad,
            estado=payload.estado,
            tags=payload.tags,
            usuario_creador=payload.usuario_creador,
            sistema_afectado=payload.sistema_afectado,
            logs=payload.logs,
            causa_raiz=payload.causa_raiz,
            pasos_diagnostico=payload.pasos_diagnostico,
            entorno=payload.entorno,
            version_sistema=payload.version_sistema,
            impacto=payload.impacto,
            resuelto_exitosamente=payload.resuelto_exitosamente,
            fecha_cierre=payload.fecha_cierre,
        ),
        auto_embed=payload.auto_embed,
    )
    return TicketCreateResponse(
        ticket=TicketResponse.model_validate(asdict(result.ticket)),
        embedding_created=result.embedding_created,
    )


@router.patch("/{ticket_id}", response_model=TicketUpdateResponse)
def update_ticket(
    ticket_id: str,
    payload: TicketUpdateRequest,
    ingestion_service: Annotated[TicketIngestionService, Depends(get_ticket_ingestion_service)],
    _admin: Annotated[ChatUserContext, Depends(require_admin_user)],
) -> TicketUpdateResponse:
    partial_payload = payload.model_dump(exclude={"auto_embed"}, exclude_unset=True)
    result = ingestion_service.update_ticket(
        ticket_id=ticket_id,
        payload=TicketUpdateInput.from_partial(partial_payload),
        auto_embed=payload.auto_embed,
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket '{ticket_id}' was not found.",
        )

    return TicketUpdateResponse(
        ticket=TicketResponse.model_validate(asdict(result.ticket)),
        embedding_refreshed=result.embedding_refreshed,
        updated_fields=result.updated_fields,
    )


@router.post("/embeddings/reindex", response_model=EmbeddingReindexResponse)
def reindex_ticket_embeddings(
    embedding_service: Annotated[TicketEmbeddingService, Depends(get_ticket_embedding_service)],
    _admin: Annotated[ChatUserContext, Depends(require_admin_user)],
    limit: int = Query(default=50, ge=1, le=500),
    mode: Literal["missing", "stale", "all"] = Query(default="missing"),
) -> EmbeddingReindexResponse:
    result = embedding_service.reindex_embeddings(limit=limit, mode=mode)
    return EmbeddingReindexResponse(
        mode=result.mode,
        processed=result.processed,
        updated=result.updated,
        failed=result.failed,
        failures=result.failures,
    )
