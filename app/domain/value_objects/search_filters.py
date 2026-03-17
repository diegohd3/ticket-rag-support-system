from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SearchFilters:
    categoria: str | None = None
    prioridad: str | None = None
    estado: str | None = None
    sistema_afectado: str | None = None
