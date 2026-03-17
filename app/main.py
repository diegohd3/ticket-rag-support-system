from __future__ import annotations

from fastapi import FastAPI

from app.api.routers.health import router as health_router
from app.api.routers.tickets import router as tickets_router
from app.infrastructure.config.settings import get_settings
from app.infrastructure.logging_config import configure_logging

settings = get_settings()

configure_logging()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Backend inicial para chatbot de soporte basado en tickets históricos. "
        "Combina búsqueda estructurada con base preparada para búsqueda semántica."
    ),
)

app.include_router(health_router)
app.include_router(tickets_router, prefix=settings.api_v1_prefix)
