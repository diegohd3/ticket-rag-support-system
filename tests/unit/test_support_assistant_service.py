from __future__ import annotations

from datetime import UTC, datetime

from app.application.interfaces.support_answer_provider import SupportAnswerProvider
from app.application.services.response_builder import ResponseBuilder
from app.application.services.support_assistant_service import SupportAssistantService
from app.application.services.ticket_search_service import RankedTicket
from app.domain.entities.ticket import Ticket


class FakeSearchService:
    def search(self, query_text: str, limit: int) -> list[RankedTicket]:
        ticket = Ticket(
            ticket_id="TCK-101",
            titulo="HTTP500 in reports",
            descripcion_problema="Report endpoint returns HTTP500",
            descripcion_solucion="Apply batching and UTC normalization",
            categoria="backend",
            prioridad="alta",
            estado="cerrado",
            fecha_creacion=datetime.now(UTC),
            fecha_cierre=None,
            tags=["http500", "reports"],
            usuario_creador="qa.user",
            sistema_afectado="reporting-service",
            logs={"error_code": "HTTP500"},
            causa_raiz="Large query batch",
            pasos_diagnostico="validate worker traces",
            entorno="prod",
            version_sistema="4.0.0",
            impacto="high",
            resuelto_exitosamente=True,
        )
        return [
            RankedTicket(
                ticket=ticket,
                relevance_score=0.9,
                text_score=1.0,
                semantic_score=0.7,
            )
        ]


class UnavailableLLMProvider(SupportAnswerProvider):
    def is_available(self) -> bool:
        return False

    def generate_support_answer(self, query_text: str, ranked_tickets: list[RankedTicket]) -> str:
        return "should not be called"


def test_assistant_falls_back_when_llm_unavailable() -> None:
    assistant = SupportAssistantService(
        ticket_search_service=FakeSearchService(),  # type: ignore[arg-type]
        response_builder=ResponseBuilder(),
        answer_provider=UnavailableLLMProvider(),
    )

    result = assistant.ask(query_text="I have HTTP500 in reports", top_k=3)
    assert result.used_llm is False
    assert "most relevant ticket is TCK-101" in result.answer
