from __future__ import annotations

from app.application.interfaces.embedding_provider import EmbeddingProvider


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """Placeholder para la integración real con la API de OpenAI."""

    def embed_text(self, text: str) -> list[float]:
        raise NotImplementedError(
            "Integración de embeddings pendiente. "
            "Este adaptador se conectará a OpenAI en la siguiente fase."
        )
