from __future__ import annotations

import re
import unicodedata

from app.domain.value_objects.search_query import SearchQuery

STOP_WORDS = {
    "a",
    "al",
    "con",
    "de",
    "del",
    "el",
    "en",
    "es",
    "la",
    "las",
    "lo",
    "los",
    "mi",
    "no",
    "por",
    "que",
    "se",
    "sin",
    "su",
    "tengo",
    "un",
    "una",
    "y",
}

ERROR_CODE_PATTERN = re.compile(r"\b(?:ERR|ERROR|HTTP|E)[-_]?\d{3,5}\b", re.IGNORECASE)
TAG_PATTERN = re.compile(r"#([a-zA-Z0-9_-]{2,50})")


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    return normalized.lower()


class QueryAnalyzer:
    def analyze(self, query_text: str) -> SearchQuery:
        normalized_text = _normalize_text(query_text).strip()
        error_codes = sorted(set(code.upper() for code in ERROR_CODE_PATTERN.findall(query_text)))
        tags = sorted(set(tag.lower() for tag in TAG_PATTERN.findall(query_text)))

        raw_tokens = re.findall(r"[a-z0-9_-]{2,50}", normalized_text)
        keywords: list[str] = []
        for token in raw_tokens:
            if token in STOP_WORDS:
                continue
            if token.startswith("err") and token[3:].isdigit():
                continue
            if token.startswith("http") and token[4:].isdigit():
                continue
            keywords.append(token)

        keywords = sorted(set(keywords))
        return SearchQuery(
            original_text=query_text,
            normalized_text=normalized_text,
            keywords=keywords,
            error_codes=error_codes,
            tags=tags,
        )
