from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SearchQuery:
    original_text: str
    normalized_text: str
    keywords: list[str]
    error_codes: list[str]
    tags: list[str]
