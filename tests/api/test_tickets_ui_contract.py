from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.api.dependencies import get_ticket_ingestion_service, get_ticket_repository
from app.application.services.ticket_ingestion_service import TicketUpdateResult
from app.domain.entities.ticket import Ticket
from app.main import app


def _ticket(ticket_id: str, titulo: str) -> Ticket:
    return Ticket(
        ticket_id=ticket_id,
        titulo=titulo,
        descripcion_problema="Problema de prueba suficientemente descriptivo",
        descripcion_solucion="Aplicar solucion recomendada",
        categoria="backend",
        prioridad="media",
        estado="cerrado",
        fecha_creacion=datetime.now(UTC),
        fecha_cierre=None,
        tags=["test"],
        usuario_creador="qa",
        sistema_afectado="api",
        logs={},
        causa_raiz=None,
        pasos_diagnostico=None,
        entorno="test",
        version_sistema="1.0.0",
        impacto="low",
        resuelto_exitosamente=True,
    )


class FakeTicketRepository:
    def __init__(self) -> None:
        self.items = [_ticket("TCK-1", "Primer ticket"), _ticket("TCK-2", "Segundo ticket")]

    def count_tickets(self) -> int:
        return 8

    def list_tickets(self, limit: int, offset: int) -> list[Ticket]:
        return self.items[offset : offset + limit]


class FakeTicketIngestionService:
    def update_ticket(self, ticket_id, payload, auto_embed=True):  # type: ignore[no-untyped-def]
        if ticket_id == "TCK-NOT-FOUND":
            return None

        ticket = _ticket(ticket_id, "Titulo actualizado")
        return TicketUpdateResult(
            ticket=ticket,
            embedding_refreshed=auto_embed,
            updated_fields=["titulo"],
        )


def test_list_tickets_returns_pagination_metadata() -> None:
    app.dependency_overrides[get_ticket_repository] = lambda: FakeTicketRepository()
    client = TestClient(app)
    response = client.get("/api/v1/tickets?limit=2&offset=0")
    payload = response.json()
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert payload["total"] == 8
    assert payload["limit"] == 2
    assert payload["offset"] == 0
    assert payload["has_next"] is True
    assert len(payload["items"]) == 2
    assert payload["items"][0]["ticket_id"] == "TCK-1"


def test_patch_ticket_returns_updated_payload() -> None:
    app.dependency_overrides[get_ticket_ingestion_service] = lambda: FakeTicketIngestionService()
    client = TestClient(app)
    response = client.patch(
        "/api/v1/tickets/TCK-77",
        json={"titulo": "Titulo actualizado", "auto_embed": True},
    )
    payload = response.json()
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert payload["embedding_refreshed"] is True
    assert payload["updated_fields"] == ["titulo"]
    assert payload["ticket"]["ticket_id"] == "TCK-77"


def test_patch_ticket_not_found_returns_standard_error() -> None:
    app.dependency_overrides[get_ticket_ingestion_service] = lambda: FakeTicketIngestionService()
    client = TestClient(app)
    response = client.patch(
        "/api/v1/tickets/TCK-NOT-FOUND",
        json={"titulo": "Titulo actualizado"},
    )
    payload = response.json()
    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert payload["code"] == "not_found"
    assert "TCK-NOT-FOUND" in payload["message"]
    assert "request_id" in payload


def test_validation_error_uses_standard_error_contract() -> None:
    client = TestClient(app)
    response = client.post("/api/v1/chat/ask", json={"query": "x", "top_k": 5})
    payload = response.json()

    assert response.status_code == 422
    assert payload["code"] == "validation_error"
    assert payload["message"] == "Request validation failed."
    assert isinstance(payload["details"], list)
    assert "request_id" in payload
