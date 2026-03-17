from __future__ import annotations

from app.application.interfaces.knowledge_provider import KnowledgeProvider


class WebSearchProvider(KnowledgeProvider):
    """Punto de extensión para fallback web futuro."""

    def search(self, query_text: str, limit: int) -> list[str]:
        raise NotImplementedError(
            "Fallback web no implementado en esta fase. "
            "Primero se prioriza exclusivamente base interna."
        )
