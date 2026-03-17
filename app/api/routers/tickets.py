from __future__ import annotations

from dataclasses import asdict
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import (
    get_response_builder,
    get_ticket_embedding_service,
    get_ticket_ingestion_service,
    get_ticket_repository,
    get_ticket_search_service,
    require_api_key,
)
from app.application.services.response_builder import ResponseBuilder
from app.application.services.ticket_embedding_service import TicketEmbeddingService
from app.application.services.ticket_ingestion_service import (
    TicketCreateInput,
    TicketIngestionService,
)
from app.application.services.ticket_search_service import TicketSearchService
from app.domain.value_objects.search_filters import SearchFilters
from app.infrastructure.config.settings import get_settings
from app.infrastructure.db.repositories.sqlalchemy_ticket_repository import (
    SqlAlchemyTicketRepository,
)
from app.schemas.search import TicketSearchResponse
from app.schemas.ticket import (
    EmbeddingReindexResponse,
    TicketCreateRequest,
    TicketCreateResponse,
    TicketResponse,
)

router = APIRouter(prefix="/tickets", tags=["tickets"], dependencies=[Depends(require_api_key)])
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
    categoria: str | None = Query(default=None),
    prioridad: str | None = Query(default=None),
    estado: str | None = Query(default=None),
    sistema_afectado: str | None = Query(default=None),
) -> TicketSearchResponse:
    filters = SearchFilters(
        categoria=categoria,
        prioridad=prioridad,
        estado=estado,
        sistema_afectado=sistema_afectado,
    )
    filters_or_none = (
        None
        if not any([filters.categoria, filters.prioridad, filters.estado, filters.sistema_afectado])
        else filters
    )
    ranked_tickets = search_service.search(query_text=query, limit=limit, filters=filters_or_none)
    response_text = response_builder.build_internal_support_response(
        query_text=query,
        ranked_tickets=ranked_tickets,
    )

    applied_filters = {
        key: value
        for key, value in {
            "categoria": categoria,
            "prioridad": prioridad,
            "estado": estado,
            "sistema_afectado": sistema_afectado,
        }.items()
        if value
    }

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


@router.post("/embeddings/reindex", response_model=EmbeddingReindexResponse)
def reindex_ticket_embeddings(
    embedding_service: Annotated[TicketEmbeddingService, Depends(get_ticket_embedding_service)],
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
