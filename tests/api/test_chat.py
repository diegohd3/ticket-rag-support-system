from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.api.dependencies import (
    ChatUserContext,
    get_support_assistant_service,
    get_user_guard_service,
    require_chat_user,
)
from app.application.services.support_assistant_service import SupportAnswerResult
from app.application.services.ticket_search_service import RankedTicket
from app.application.services.user_guard_service import QueryGuardResult
from app.domain.entities.ticket import Ticket
from app.main import app


class FakeAssistant:
    def ask(self, query_text: str, top_k: int, filters=None) -> SupportAnswerResult:
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
            confidence=0.91,
            evidence_ticket_ids=["TCK-FAKE-1"],
        )


class FakeUserGuard:
    def evaluate_query(self, user_id: str, query_text: str) -> QueryGuardResult:
        return QueryGuardResult(allowed=True, blocked=False, reason=None, violation_count=0)

    def mark_success(self, user_id: str) -> None:
        return None


def test_chat_ask_endpoint_returns_response() -> None:
    app.dependency_overrides[get_support_assistant_service] = lambda: FakeAssistant()
    app.dependency_overrides[require_chat_user] = lambda: ChatUserContext(
        user_id="test-user",
        display_name="Tester",
    )
    app.dependency_overrides[get_user_guard_service] = lambda: FakeUserGuard()
    client = TestClient(app)
    response = client.post("/api/v1/chat/ask", json={"query": "error in service", "top_k": 3})
    payload = response.json()
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert payload["used_llm"] is False
    assert payload["confidence"] == 0.91
    assert payload["results_count"] == 1
    assert payload["sources"][0]["ticket_id"] == "TCK-FAKE-1"
