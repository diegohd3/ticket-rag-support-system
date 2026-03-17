from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.dependencies import ChatUserContext, get_user_guard_service, require_chat_user
from app.application.services.user_guard_service import QueryGuardResult
from app.main import app


class FakeGuardOffTopic:
    def evaluate_query(self, user_id: str, query_text: str) -> QueryGuardResult:
        return QueryGuardResult(
            allowed=False,
            blocked=False,
            reason="off_topic_query",
            violation_count=2,
        )

    def mark_success(self, user_id: str) -> None:
        return None


class FakeGuardBlocked:
    def evaluate_query(self, user_id: str, query_text: str) -> QueryGuardResult:
        return QueryGuardResult(
            allowed=False,
            blocked=True,
            reason="off_topic_query",
            violation_count=3,
        )

    def mark_success(self, user_id: str) -> None:
        return None


def _fake_user_context() -> ChatUserContext:
    return ChatUserContext(user_id="qa-user", display_name="QA")


def test_chat_guard_rejects_off_topic_queries() -> None:
    app.dependency_overrides[require_chat_user] = _fake_user_context
    app.dependency_overrides[get_user_guard_service] = lambda: FakeGuardOffTopic()

    client = TestClient(app)
    response = client.post("/api/v1/chat/ask", json={"query": "horoscopo hoy", "top_k": 5})
    payload = response.json()

    app.dependency_overrides.clear()

    assert response.status_code == 422
    assert payload["code"] == "unsupported_query"


def test_chat_guard_blocks_user_after_repeated_violations() -> None:
    app.dependency_overrides[require_chat_user] = _fake_user_context
    app.dependency_overrides[get_user_guard_service] = lambda: FakeGuardBlocked()

    client = TestClient(app)
    response = client.post("/api/v1/chat/ask", json={"query": "horoscopo hoy", "top_k": 5})
    payload = response.json()

    app.dependency_overrides.clear()

    assert response.status_code == 403
    assert payload["code"] == "user_blocked"
