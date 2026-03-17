from __future__ import annotations

from dataclasses import dataclass

from app.domain.value_objects.search_filters import SearchFilters


@dataclass(slots=True)
class SearchQuery:
    original_text: str
    normalized_text: str
    keywords: list[str]
    error_codes: list[str]
    tags: list[str]
    filters: SearchFilters | None = None
