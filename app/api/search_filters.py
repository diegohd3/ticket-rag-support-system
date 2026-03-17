from __future__ import annotations

from app.domain.value_objects.search_filters import SearchFilters


def build_optional_search_filters(
    *,
    categoria: str | None,
    prioridad: str | None,
    estado: str | None,
    sistema_afectado: str | None,
) -> SearchFilters | None:
    filters = SearchFilters(
        categoria=categoria,
        prioridad=prioridad,
        estado=estado,
        sistema_afectado=sistema_afectado,
    )
    if not any((filters.categoria, filters.prioridad, filters.estado, filters.sistema_afectado)):
        return None
    return filters


def build_applied_filters(
    *,
    categoria: str | None,
    prioridad: str | None,
    estado: str | None,
    sistema_afectado: str | None,
) -> dict[str, str]:
    return {
        key: value
        for key, value in {
            "categoria": categoria,
            "prioridad": prioridad,
            "estado": estado,
            "sistema_afectado": sistema_afectado,
        }.items()
        if value
    }
