from __future__ import annotations

from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import ChatUserContext, require_admin_user, require_api_key
from app.infrastructure.observability.runtime_metrics import runtime_metrics
from app.schemas.ops import RuntimeMetricsResponse

router = APIRouter(prefix="/ops", tags=["ops"], dependencies=[Depends(require_api_key)])


@router.get("/metrics", response_model=RuntimeMetricsResponse)
def get_runtime_metrics(
    _admin: Annotated[ChatUserContext, Depends(require_admin_user)],
) -> RuntimeMetricsResponse:
    snapshot = runtime_metrics.snapshot()
    return RuntimeMetricsResponse(
        started_at_unix=snapshot.started_at_unix,
        total_requests=snapshot.total_requests,
        total_errors=snapshot.total_errors,
        avg_latency_ms=snapshot.avg_latency_ms,
        requests_by_path=snapshot.requests_by_path,
        openai=asdict(snapshot.openai),
    )
