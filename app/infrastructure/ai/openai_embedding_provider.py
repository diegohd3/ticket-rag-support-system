from __future__ import annotations

from openai import OpenAI

from app.application.interfaces.embedding_provider import EmbeddingProvider
from app.infrastructure.config.settings import Settings
from app.infrastructure.observability.runtime_metrics import runtime_metrics


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

        try:
            response = self._client.embeddings.create(
                model=self._settings.embedding_model,
                input=text,
            )
        except Exception:  # noqa: BLE001
            runtime_metrics.record_embedding_call(success=False)
            raise

        input_tokens = int(getattr(getattr(response, "usage", None), "prompt_tokens", 0) or 0)
        estimated_cost = (
            input_tokens / 1_000_000
        ) * self._settings.embedding_input_cost_per_1m_tokens
        runtime_metrics.record_embedding_call(
            success=True,
            input_tokens=input_tokens,
            estimated_cost_usd=estimated_cost,
        )
        return response.data[0].embedding

    def is_available(self) -> bool:
        return self._client is not None
