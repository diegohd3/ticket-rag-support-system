from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.dependencies import ChatUserContext, get_ticket_embedding_service, require_admin_user
from app.application.services.ticket_embedding_service import EmbeddingReindexResult
from app.main import app


class FakeEmbeddingService:
    def reindex_embeddings(self, limit: int, mode: str = "missing") -> EmbeddingReindexResult:
        assert limit == 10
        assert mode == "stale"
        return EmbeddingReindexResult(
            mode="stale",
            processed=3,
            updated=3,
            failed=0,
            failures=[],
        )


def test_reindex_endpoint_accepts_mode() -> None:
    app.dependency_overrides[get_ticket_embedding_service] = lambda: FakeEmbeddingService()
    app.dependency_overrides[require_admin_user] = lambda: ChatUserContext(
        user_id="admin",
        display_name="Admin",
        is_admin=True,
    )
    client = TestClient(app)
    response = client.post("/api/v1/tickets/embeddings/reindex?limit=10&mode=stale")
    payload = response.json()
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert payload["mode"] == "stale"
    assert payload["processed"] == 3
    assert payload["updated"] == 3
    assert payload["failed"] == 0
