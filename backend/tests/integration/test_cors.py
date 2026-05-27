"""Testes da configuração CORS da API."""

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app


def test_cors_permite_origem_configurada(monkeypatch) -> None:
    """Preflight CORS retorna headers para origem configurada."""
    monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com")
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.options(
        "/api/v1/pedidos",
        headers={
            "Origin": "https://app.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://app.example.com"


def test_cors_nao_envia_header_sem_origem_configurada(monkeypatch) -> None:
    """Origem não configurada não recebe permissão CORS."""
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.options(
        "/api/v1/pedidos",
        headers={
            "Origin": "https://app.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert "access-control-allow-origin" not in response.headers
