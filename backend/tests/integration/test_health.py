"""Testes do endpoint de health-check."""

from fastapi.testclient import TestClient


def test_health_endpoint_retorna_200_e_payload_ok(client: TestClient) -> None:
    """GET /health responde 200 com `{"status": "ok"}`."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
