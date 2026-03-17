from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.api.dependencies import get_support_assistant_service
from app.application.services.support_assistant_service import SupportAnswerResult
from app.application.services.ticket_search_service import RankedTicket
from app.domain.entities.ticket import Ticket
from app.main import app


class FakeAssistant:
    def ask(self, query_text: str, top_k: int) -> SupportAnswerResult:
        ticket = Ticket(
            ticket_id="TCK-FAKE-1",
            titulo="Sample incident",
            descripcion_problema="Sample issue",
            descripcion_solucion="Sample solution",
            categoria="demo",
            prioridad="media",
            estado="cerrado",
            fecha_creacion=datetime.now(UTC),
            fecha_cierre=None,
            tags=["demo"],
            usuario_creador="tester",
            sistema_afectado="demo-system",
            logs={},
            causa_raiz=None,
            pasos_diagnostico=None,
            entorno=None,
            version_sistema=None,
            impacto=None,
            resuelto_exitosamente=True,
        )
        return SupportAnswerResult(
            query=query_text,
            answer="Use the known workaround from TCK-FAKE-1.",
            ranked_tickets=[
                RankedTicket(
                    ticket=ticket,
                    relevance_score=0.91,
                    text_score=0.8,
                    semantic_score=0.95,
                )
            ],
            used_llm=False,
        )


def test_chat_ask_endpoint_returns_response() -> None:
    app.dependency_overrides[get_support_assistant_service] = lambda: FakeAssistant()
    client = TestClient(app)
    response = client.post("/api/v1/chat/ask", json={"query": "error in service", "top_k": 3})
    payload = response.json()
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert payload["used_llm"] is False
    assert payload["results_count"] == 1
    assert payload["sources"][0]["ticket_id"] == "TCK-FAKE-1"
