from __future__ import annotations

import logging
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routers.chat import router as chat_router
from app.api.routers.demo import router as demo_router
from app.api.routers.health import router as health_router
from app.api.routers.ops import router as ops_router
from app.api.routers.tickets import router as tickets_router
from app.infrastructure.config.settings import get_settings
from app.infrastructure.logging_config import configure_logging
from app.infrastructure.observability.rate_limiter import InMemoryRateLimiter
from app.infrastructure.observability.runtime_metrics import runtime_metrics

settings = get_settings()
configure_logging()
logger = logging.getLogger(__name__)
rate_limiter = InMemoryRateLimiter(
    max_requests=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window_seconds,
)

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
    request_id = request.headers.get("x-request-id") or uuid4().hex
    path = request.url.path

    if settings.rate_limit_enabled and path.startswith(settings.api_v1_prefix):
        client = request.headers.get("x-forwarded-for")
        client_ip = (
            client.split(",")[0].strip()
            if client
            else (request.client.host if request.client else "unknown")
        )
        rate_limit_key = f"{client_ip}:{path}"
        if not rate_limiter.allow(rate_limit_key):
            response = JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please retry later.",
                    "request_id": request_id,
                },
            )
            response.headers["X-Request-ID"] = request_id
            if settings.observability_enabled:
                runtime_metrics.record_request(path=path, status_code=429, duration_ms=0.0)
            return response

    started_at = perf_counter()
    response = await call_next(request)
    elapsed_ms = round((perf_counter() - started_at) * 1000, 2)
    response.headers["X-Process-Time-ms"] = f"{elapsed_ms:.2f}"
    response.headers["X-Request-ID"] = request_id
    if settings.observability_enabled:
        runtime_metrics.record_request(
            path=path,
            status_code=response.status_code,
            duration_ms=elapsed_ms,
        )
    logger.info(
        "request_id=%s method=%s path=%s status=%s duration_ms=%.2f",
        request_id,
        request.method,
        path,
        response.status_code,
        elapsed_ms,
    )
    return response


app.include_router(health_router)
app.include_router(tickets_router, prefix=settings.api_v1_prefix)
app.include_router(chat_router, prefix=settings.api_v1_prefix)
app.include_router(ops_router, prefix=settings.api_v1_prefix)
app.include_router(demo_router)
