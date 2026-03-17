from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.application.services.query_analyzer import QueryAnalyzer
from app.application.services.response_builder import ResponseBuilder
from app.application.services.support_assistant_service import SupportAssistantService
from app.application.services.ticket_embedding_service import TicketEmbeddingService
from app.application.services.ticket_ingestion_service import TicketIngestionService
from app.application.services.ticket_search_service import TicketSearchService
from app.application.services.user_guard_service import UserGuardService
from app.infrastructure.ai.openai_embedding_provider import OpenAIEmbeddingProvider
from app.infrastructure.ai.openai_support_answer_provider import OpenAISupportAnswerProvider
from app.infrastructure.config.settings import Settings, get_settings
from app.infrastructure.db.repositories.sqlalchemy_support_user_repository import (
    SqlAlchemySupportUserRepository,
)
from app.infrastructure.db.repositories.sqlalchemy_ticket_repository import (
    SqlAlchemyTicketRepository,
)
from app.infrastructure.db.session import get_db_session


def get_db() -> Generator[Session, None, None]:
    yield from get_db_session()


def get_settings_dependency() -> Settings:
    return get_settings()


def get_ticket_repository(
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings_dependency)],
) -> SqlAlchemyTicketRepository:
    return SqlAlchemyTicketRepository(db, vector_probes=settings.vector_search_probes)


def get_support_user_repository(
    db: Annotated[Session, Depends(get_db)],
) -> SqlAlchemySupportUserRepository:
    return SqlAlchemySupportUserRepository(db)


def get_query_analyzer() -> QueryAnalyzer:
    return QueryAnalyzer()


def get_embedding_provider(
    settings: Annotated[Settings, Depends(get_settings_dependency)],
) -> OpenAIEmbeddingProvider:
    return OpenAIEmbeddingProvider(settings=settings)


def get_ticket_search_service(
    repository: Annotated[SqlAlchemyTicketRepository, Depends(get_ticket_repository)],
    analyzer: Annotated[QueryAnalyzer, Depends(get_query_analyzer)],
    settings: Annotated[Settings, Depends(get_settings_dependency)],
    embedding_provider: Annotated[OpenAIEmbeddingProvider, Depends(get_embedding_provider)],
) -> TicketSearchService:
    return TicketSearchService(
        repository=repository,
        analyzer=analyzer,
        embedding_provider=embedding_provider,
        candidate_limit=settings.search_candidate_limit,
        semantic_candidate_limit=settings.semantic_candidate_limit,
        semantic_search_enabled=settings.semantic_search_enabled,
        text_weight=settings.hybrid_text_weight,
        semantic_weight=settings.hybrid_semantic_weight,
        rerank_enabled=settings.rerank_enabled,
        rerank_window=settings.rerank_window,
    )


def get_response_builder() -> ResponseBuilder:
    return ResponseBuilder()


def get_support_answer_provider(
    settings: Annotated[Settings, Depends(get_settings_dependency)],
) -> OpenAISupportAnswerProvider:
    return OpenAISupportAnswerProvider(settings=settings)


def get_support_assistant_service(
    search_service: Annotated[TicketSearchService, Depends(get_ticket_search_service)],
    response_builder: Annotated[ResponseBuilder, Depends(get_response_builder)],
    answer_provider: Annotated[OpenAISupportAnswerProvider, Depends(get_support_answer_provider)],
) -> SupportAssistantService:
    return SupportAssistantService(
        ticket_search_service=search_service,
        response_builder=response_builder,
        answer_provider=answer_provider,
    )


def get_ticket_embedding_service(
    repository: Annotated[SqlAlchemyTicketRepository, Depends(get_ticket_repository)],
    embedding_provider: Annotated[OpenAIEmbeddingProvider, Depends(get_embedding_provider)],
    settings: Annotated[Settings, Depends(get_settings_dependency)],
) -> TicketEmbeddingService:
    return TicketEmbeddingService(
        repository=repository,
        embedding_provider=embedding_provider,
        embedding_model=settings.embedding_model,
        batch_size=settings.embedding_reindex_batch_size,
    )


def get_ticket_ingestion_service(
    repository: Annotated[SqlAlchemyTicketRepository, Depends(get_ticket_repository)],
    embedding_service: Annotated[TicketEmbeddingService, Depends(get_ticket_embedding_service)],
) -> TicketIngestionService:
    return TicketIngestionService(repository=repository, embedding_service=embedding_service)


def get_user_guard_service(
    user_repository: Annotated[
        SqlAlchemySupportUserRepository,
        Depends(get_support_user_repository),
    ],
    settings: Annotated[Settings, Depends(get_settings_dependency)],
) -> UserGuardService:
    return UserGuardService(
        user_repository=user_repository,
        violation_threshold=settings.user_violation_threshold,
        enabled=settings.user_guard_enabled,
    )


@dataclass(slots=True)
class ChatUserContext:
    user_id: str
    display_name: str | None


def require_chat_user(
    request: Request,
    guard_service: Annotated[UserGuardService, Depends(get_user_guard_service)],
) -> ChatUserContext:
    raw_user_id = request.headers.get("x-user-id", "").strip()
    raw_display_name = request.headers.get("x-user-name", "").strip()
    display_name = raw_display_name or None

    if not raw_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "user_identification_required",
                "message": "X-User-Id header is required for chat access.",
            },
        )

    user = guard_service.ensure_user(user_id=raw_user_id, display_name=display_name)
    if user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "user_blocked",
                "message": "This user account is blocked due repeated policy violations.",
            },
        )

    return ChatUserContext(user_id=user.user_id, display_name=user.display_name)


def require_api_key(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings_dependency)],
) -> None:
    if not settings.api_key_required:
        return

    if not settings.internal_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key auth is enabled but INTERNAL_API_KEY is not configured.",
        )

    provided = request.headers.get("x-api-key", "")
    if provided != settings.internal_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )
