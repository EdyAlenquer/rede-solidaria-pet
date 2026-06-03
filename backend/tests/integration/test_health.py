"""Testes dos endpoints de health-check (liveness e readiness)."""

from collections.abc import Iterator

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.database import get_db
from app.main import app


def test_health_endpoint_retorna_200_e_payload_ok(client: TestClient) -> None:
    """GET /health responde 200 com `{"status": "ok"}` (liveness estático)."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_endpoint_retorna_200_quando_banco_responde(api_client: TestClient) -> None:
    """GET /ready responde 200 com `{"status": "ready"}` quando o banco responde."""
    response = api_client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_ready_endpoint_retorna_503_quando_banco_falha(client: TestClient) -> None:
    """GET /ready responde 503 ProblemDetail quando o `SELECT 1` falha."""

    class _BrokenSession:
        """Sessão falsa cujo `execute` falha, simulando banco indisponível."""

        def execute(self, *args, **kwargs):  # noqa: ANN002, ANN003, ANN201, ARG002
            raise OperationalError("SELECT 1", {}, Exception("banco fora do ar"))

    def _broken_get_db() -> Iterator[_BrokenSession]:
        """Override de `get_db` que rende uma sessão que falha no `execute`."""
        yield _BrokenSession()

    app.dependency_overrides[get_db] = _broken_get_db
    try:
        response = client.get("/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.headers["content-type"] == "application/problem+json"
    body = response.json()
    assert body["status"] == 503
    assert body["title"] == "Serviço indisponível"
