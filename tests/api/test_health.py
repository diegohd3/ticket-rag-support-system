from fastapi.testclient import TestClient

from app.main import app


def test_healthcheck_returns_ok() -> None:
    client = TestClient(app)
    response = client.get("/health")
    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "ok"
    assert payload["app_name"] == "AI Support Ticket Chatbot"
