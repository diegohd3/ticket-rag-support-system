from __future__ import annotations

from openai import OpenAI

from app.application.interfaces.support_answer_provider import SupportAnswerProvider
from app.application.services.ticket_search_service import RankedTicket
from app.infrastructure.config.settings import Settings
from app.infrastructure.observability.runtime_metrics import runtime_metrics


class OpenAISupportAnswerProvider(SupportAnswerProvider):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = (
            OpenAI(api_key=settings.openai_api_key, timeout=settings.openai_timeout_seconds)
            if settings.openai_api_key
            else None
        )

    def is_available(self) -> bool:
        return self._client is not None

    def generate_support_answer(self, query_text: str, ranked_tickets: list[RankedTicket]) -> str:
        if not self._client:
            raise RuntimeError("OPENAI_API_KEY is required to generate support answers.")

        context_sections = []
        for ranked in ranked_tickets[: self._settings.chat_max_context_tickets]:
            ticket = ranked.ticket
            section = (
                f"[{ticket.ticket_id}] title={ticket.titulo}\n"
                f"problem={ticket.descripcion_problema}\n"
                f"solution={ticket.descripcion_solucion}\n"
                f"diagnostic_steps={ticket.pasos_diagnostico or 'N/A'}\n"
                f"tags={', '.join(ticket.tags)}\n"
                f"affected_system={ticket.sistema_afectado}\n"
                f"hybrid_score={ranked.relevance_score:.4f}"
            )
            context_sections.append(section)

        context_blob = "\n\n".join(context_sections)
        system_prompt = (
            "You are a senior technical support assistant. "
            "Answer only with evidence from provided internal tickets. "
            "If evidence is weak, say so and ask for missing diagnostics. "
            "Always be concise, professional, and actionable."
        )
        user_prompt = (
            f"User issue:\n{query_text}\n\n"
            f"Internal ticket evidence:\n{context_blob}\n\n"
            "Provide:\n"
            "1) Short diagnosis\n"
            "2) Recommended steps in order\n"
            "3) Risks or validation checks\n"
            "4) Ticket references used (ticket IDs)"
        )

        try:
            response = self._client.responses.create(
                model=self._settings.openai_model,
                instructions=system_prompt,
                input=user_prompt,
            )
        except Exception:  # noqa: BLE001
            runtime_metrics.record_llm_call(success=False)
            raise

        usage = getattr(response, "usage", None)
        input_tokens = int(getattr(usage, "input_tokens", 0) or 0)
        output_tokens = int(getattr(usage, "output_tokens", 0) or 0)
        estimated_cost = (
            (input_tokens / 1_000_000) * self._settings.llm_input_cost_per_1m_tokens
        ) + ((output_tokens / 1_000_000) * self._settings.llm_output_cost_per_1m_tokens)
        runtime_metrics.record_llm_call(
            success=True,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=estimated_cost,
        )
        return response.output_text.strip()
