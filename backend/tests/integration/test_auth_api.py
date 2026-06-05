"""Testes de integração dos endpoints de autenticação."""

from fastapi.testclient import TestClient

_REGISTRO_VALIDO = {
    "nome": "Ana Protetora",
    "email": "ana@example.com",
    "senha": "senha-com-8+",
    "consentimento_aceito": True,
}


def test_post_registro_cria_usuario_201_sem_senha(api_client: TestClient) -> None:
    """POST /auth/registro cria o usuário, retorna 201 e UsuarioRead sem senha."""
    r = api_client.post("/api/v1/auth/registro", json=_REGISTRO_VALIDO)

    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "ana@example.com"
    assert body["papel"] == "protetor"
    assert "senha" not in body
    assert "senha_hash" not in body


def test_post_registro_email_duplicado_retorna_409(api_client: TestClient) -> None:
    """Registrar o mesmo e-mail duas vezes retorna 409 ProblemDetail."""
    api_client.post("/api/v1/auth/registro", json=_REGISTRO_VALIDO)

    r = api_client.post("/api/v1/auth/registro", json=_REGISTRO_VALIDO)

    assert r.status_code == 409
    assert r.headers["content-type"] == "application/problem+json"
    assert r.json()["title"] == "E-mail já cadastrado"


def test_post_registro_sem_consentimento_retorna_422(api_client: TestClient) -> None:
    """Registro sem aceitar o consentimento LGPD retorna 422."""
    payload = {**_REGISTRO_VALIDO, "consentimento_aceito": False}

    r = api_client.post("/api/v1/auth/registro", json=payload)

    assert r.status_code == 422
    assert r.json()["title"] == "Erro de validação"


def test_post_registro_senha_curta_retorna_422(api_client: TestClient) -> None:
    """Registro com senha menor que 8 caracteres retorna 422."""
    payload = {**_REGISTRO_VALIDO, "senha": "1234567"}

    r = api_client.post("/api/v1/auth/registro", json=payload)

    assert r.status_code == 422


def test_post_login_credenciais_validas_retorna_token(api_client: TestClient) -> None:
    """POST /auth/login com credenciais corretas retorna 200 e access token."""
    api_client.post("/api/v1/auth/registro", json=_REGISTRO_VALIDO)

    r = api_client.post(
        "/api/v1/auth/login",
        json={"email": "ana@example.com", "senha": "senha-com-8+"},
    )

    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)
    assert body["access_token"]


def test_post_login_senha_errada_retorna_401(api_client: TestClient) -> None:
    """POST /auth/login com senha incorreta retorna 401 ProblemDetail."""
    api_client.post("/api/v1/auth/registro", json=_REGISTRO_VALIDO)

    r = api_client.post(
        "/api/v1/auth/login",
        json={"email": "ana@example.com", "senha": "errada"},
    )

    assert r.status_code == 401
    assert r.json()["title"] == "Credenciais inválidas"


def test_post_login_email_inexistente_retorna_401(api_client: TestClient) -> None:
    """POST /auth/login com e-mail inexistente retorna 401."""
    r = api_client.post(
        "/api/v1/auth/login",
        json={"email": "ninguem@example.com", "senha": "qualquer"},
    )

    assert r.status_code == 401


def test_get_me_com_token_retorna_usuario(api_client: TestClient, auth_headers: dict) -> None:
    """GET /auth/me com Bearer válido retorna o usuário autenticado."""
    r = api_client.get("/api/v1/auth/me", headers=auth_headers)

    assert r.status_code == 200
    body = r.json()
    assert body["email"]
    assert "senha_hash" not in body


def test_get_me_sem_token_retorna_401(api_client: TestClient) -> None:
    """GET /auth/me sem Authorization retorna 401."""
    r = api_client.get("/api/v1/auth/me")

    assert r.status_code == 401


def test_get_me_token_invalido_retorna_401(api_client: TestClient) -> None:
    """GET /auth/me com token malformado retorna 401."""
    r = api_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer isto.nao.e-token"},
    )

    assert r.status_code == 401
