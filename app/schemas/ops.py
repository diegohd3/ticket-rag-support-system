from __future__ import annotations

from pydantic import BaseModel


class OpenAIMetricsResponse(BaseModel):
    embedding_calls: int
    embedding_failures: int
    llm_calls: int
    llm_failures: int
    embedding_input_tokens: int
    llm_input_tokens: int
    llm_output_tokens: int
    estimated_cost_usd: float


class RuntimeMetricsResponse(BaseModel):
    started_at_unix: float
    total_requests: int
    total_errors: int
    avg_latency_ms: float
    requests_by_path: dict[str, int]
    openai: OpenAIMetricsResponse
