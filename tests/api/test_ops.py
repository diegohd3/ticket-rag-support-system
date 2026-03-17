from fastapi.testclient import TestClient

from app.main import app


def test_ops_metrics_endpoint_returns_runtime_snapshot() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/ops/metrics")
    payload = response.json()

    assert response.status_code == 200
    assert "total_requests" in payload
    assert "avg_latency_ms" in payload
    assert "openai" in payload
