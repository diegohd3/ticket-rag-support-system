from __future__ import annotations

from openai import OpenAI

from app.application.interfaces.embedding_provider import EmbeddingProvider
from app.infrastructure.config.settings import Settings


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = (
            OpenAI(api_key=settings.openai_api_key, timeout=settings.openai_timeout_seconds)
            if settings.openai_api_key
            else None
        )

    def embed_text(self, text: str) -> list[float]:
        if not self._client:
            raise RuntimeError("OPENAI_API_KEY is required to generate embeddings.")

        response = self._client.embeddings.create(
            model=self._settings.embedding_model,
            input=text,
        )
        return response.data[0].embedding

    def is_available(self) -> bool:
        return self._client is not None
