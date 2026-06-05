"""Testes da Fase B3 — observabilidade e hardening.

Cobre request-id middleware, security headers, docs desligado em produção,
CORS restrito e rate limiting (429) via override de Settings.
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.core.rate_limit import aplicar_estado_limiter, limiter
from app.main import create_app


@pytest.fixture
def settings_limpas() -> Iterator[None]:
    """Limpa o cache de `get_settings` e restaura o estado do rate limiter.

    Garante que mudanças de variáveis de ambiente sejam refletidas em uma nova
    instância de Settings e não vazem para outros testes. No teardown, reseta o
    estado do limiter compartilhado (enabled + storage) para não contaminar a
    `app` singleton usada por outros testes.

    Yields:
        None.
    """
    get_settings.cache_clear()
    try:
        yield
    finally:
        get_settings.cache_clear()
        limiter.reset()
        aplicar_estado_limiter()


def test_request_id_gerado_e_devolvido_no_header(client: TestClient) -> None:
    """Toda resposta inclui um `X-Request-Id` quando o cliente não envia um."""
    response = client.get("/health")

    assert response.status_code == 200
    request_id = response.headers.get("x-request-id")
    assert request_id
    assert len(request_id) >= 8


def test_request_id_do_cliente_e_propagado(client: TestClient) -> None:
    """Quando o cliente envia `X-Request-Id`, o mesmo valor volta na resposta."""
    response = client.get("/health", headers={"X-Request-Id": "meu-id-fixo-123"})

    assert response.headers.get("x-request-id") == "meu-id-fixo-123"


def test_request_id_aparece_no_problem_detail_instance(api_client: TestClient) -> None:
    """Em erro, o `instance` do ProblemDetail carrega o request-id da requisição."""
    response = api_client.get("/api/v1/pedidos/999999", headers={"X-Request-Id": "id-de-erro-abc"})

    assert response.status_code == 404
    body = response.json()
    assert "id-de-erro-abc" in body["instance"]


def test_security_headers_presentes_em_toda_resposta(client: TestClient) -> None:
    """Headers de segurança básicos aparecem em toda resposta."""
    response = client.get("/health")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert "default-src" in response.headers["content-security-policy"]


def test_hsts_ausente_em_desenvolvimento(client: TestClient) -> None:
    """Em desenvolvimento, o header HSTS não é enviado."""
    response = client.get("/health")

    assert "strict-transport-security" not in response.headers


def test_hsts_presente_em_producao(settings_limpas, monkeypatch) -> None:
    """Em produção, o header HSTS é enviado."""
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "uma-chave-bem-secreta-e-unica-para-prod")
    app_prod = create_app()
    client = TestClient(app_prod)

    response = client.get("/health")

    assert "strict-transport-security" in response.headers


def test_docs_desligado_em_producao(settings_limpas, monkeypatch) -> None:
    """Em produção, `/docs`, `/redoc` e `/openapi.json` respondem 404."""
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "uma-chave-bem-secreta-e-unica-para-prod")
    app_prod = create_app()
    client = TestClient(app_prod)

    assert client.get("/docs").status_code == 404
    assert client.get("/redoc").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_docs_ligado_em_desenvolvimento(client: TestClient) -> None:
    """Em desenvolvimento, `/docs` continua disponível (200)."""
    assert client.get("/docs").status_code == 200


def test_cors_restringe_metodos_e_headers(settings_limpas, monkeypatch) -> None:
    """O preflight CORS só permite os métodos e headers explicitamente liberados."""
    monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com")
    app_cors = create_app()
    client = TestClient(app_cors)

    response = client.options(
        "/api/v1/pedidos",
        headers={
            "Origin": "https://app.example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization",
        },
    )

    assert response.status_code == 200
    metodos = response.headers["access-control-allow-methods"]
    assert "GET" in metodos and "POST" in metodos and "PATCH" in metodos
    assert "*" not in metodos


def test_rate_limit_retorna_429_quando_excede(settings_limpas, monkeypatch, db_session) -> None:
    """Com limite baixo via override, o segundo login excede e retorna 429."""
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("RATE_LIMIT_AUTH", "1/minute")
    from app.database import get_db

    def _override_get_db() -> Iterator:
        yield db_session

    app_rl = create_app()
    app_rl.dependency_overrides[get_db] = _override_get_db
    client = TestClient(app_rl)

    payload = {"email": "ninguem@example.com", "senha": "qualquer-senha-1234"}
    primeira = client.post("/api/v1/auth/login", json=payload)
    segunda = client.post("/api/v1/auth/login", json=payload)

    assert primeira.status_code in (401, 422)
    assert segunda.status_code == 429
