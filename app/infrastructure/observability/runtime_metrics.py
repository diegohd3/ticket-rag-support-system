from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from time import time


@dataclass(slots=True)
class OpenAIMetrics:
    embedding_calls: int = 0
    embedding_failures: int = 0
    llm_calls: int = 0
    llm_failures: int = 0
    embedding_input_tokens: int = 0
    llm_input_tokens: int = 0
    llm_output_tokens: int = 0
    estimated_cost_usd: float = 0.0


@dataclass(slots=True)
class RuntimeMetricsSnapshot:
    started_at_unix: float
    total_requests: int
    total_errors: int
    avg_latency_ms: float
    requests_by_path: dict[str, int]
    openai: OpenAIMetrics


class RuntimeMetricsStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._started_at_unix = time()
        self._total_requests = 0
        self._total_errors = 0
        self._total_latency_ms = 0.0
        self._requests_by_path: dict[str, int] = {}
        self._openai = OpenAIMetrics()

    def record_request(self, path: str, status_code: int, duration_ms: float) -> None:
        with self._lock:
            self._total_requests += 1
            if status_code >= 400:
                self._total_errors += 1
            self._total_latency_ms += duration_ms
            self._requests_by_path[path] = self._requests_by_path.get(path, 0) + 1

    def record_embedding_call(
        self,
        success: bool,
        input_tokens: int = 0,
        estimated_cost_usd: float = 0.0,
    ) -> None:
        with self._lock:
            self._openai.embedding_calls += 1
            if not success:
                self._openai.embedding_failures += 1
            self._openai.embedding_input_tokens += max(0, input_tokens)
            self._openai.estimated_cost_usd += max(0.0, estimated_cost_usd)

    def record_llm_call(
        self,
        success: bool,
        input_tokens: int = 0,
        output_tokens: int = 0,
        estimated_cost_usd: float = 0.0,
    ) -> None:
        with self._lock:
            self._openai.llm_calls += 1
            if not success:
                self._openai.llm_failures += 1
            self._openai.llm_input_tokens += max(0, input_tokens)
            self._openai.llm_output_tokens += max(0, output_tokens)
            self._openai.estimated_cost_usd += max(0.0, estimated_cost_usd)

    def snapshot(self) -> RuntimeMetricsSnapshot:
        with self._lock:
            avg_latency = (
                self._total_latency_ms / self._total_requests if self._total_requests > 0 else 0.0
            )
            return RuntimeMetricsSnapshot(
                started_at_unix=self._started_at_unix,
                total_requests=self._total_requests,
                total_errors=self._total_errors,
                avg_latency_ms=round(avg_latency, 4),
                requests_by_path=dict(self._requests_by_path),
                openai=OpenAIMetrics(
                    embedding_calls=self._openai.embedding_calls,
                    embedding_failures=self._openai.embedding_failures,
                    llm_calls=self._openai.llm_calls,
                    llm_failures=self._openai.llm_failures,
                    embedding_input_tokens=self._openai.embedding_input_tokens,
                    llm_input_tokens=self._openai.llm_input_tokens,
                    llm_output_tokens=self._openai.llm_output_tokens,
                    estimated_cost_usd=round(self._openai.estimated_cost_usd, 6),
                ),
            )


runtime_metrics = RuntimeMetricsStore()
