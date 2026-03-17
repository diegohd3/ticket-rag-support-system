from __future__ import annotations

import logging
from time import perf_counter

from fastapi import FastAPI, Request

from app.api.routers.chat import router as chat_router
from app.api.routers.health import router as health_router
from app.api.routers.tickets import router as tickets_router
from app.infrastructure.config.settings import get_settings
from app.infrastructure.logging_config import configure_logging

settings = get_settings()
configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Support chatbot backend using structured + semantic retrieval with "
        "RAG-ready architecture on top of historical tickets."
    ),
)


@app.middleware("http")
async def request_metrics_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
    started_at = perf_counter()
    response = await call_next(request)
    elapsed_ms = (perf_counter() - started_at) * 1000
    response.headers["X-Process-Time-ms"] = f"{elapsed_ms:.2f}"
    logger.info(
        "request method=%s path=%s status=%s duration_ms=%.2f",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response


app.include_router(health_router)
app.include_router(tickets_router, prefix=settings.api_v1_prefix)
app.include_router(chat_router, prefix=settings.api_v1_prefix)
