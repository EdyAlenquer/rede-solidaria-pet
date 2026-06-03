"""Testes de integração dos direitos do titular (LGPD): exportação e exclusão.

Cobre os endpoints da Fase B4:

- ``GET /api/v1/me/dados`` — direito de acesso (exportação dos dados pessoais).
- ``DELETE /api/v1/me`` — direito de eliminação (anonimização + soft-delete).
- ``DELETE /api/v1/admin/usuarios/{id}`` — exclusão/anonimização por admin.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.usuario import Usuario

_PEDIDO_PAYLOAD = {
    "titulo": "Gata abandonada precisa de lar",
    "descricao": "Encontrada no bairro central, precisa de cuidados e adoção.",
    "categoria": "lar_temporario",
    "urgencia": "media",
    "contato": "11988887777",
    "cidade": "Campinas",
    "estado": "SP",
    "consentimento_aceito": True,
}


def _criar_pedido(api_client: TestClient, auth_headers: dict) -> dict:
    """Cria um pedido válido autenticado e retorna o corpo da resposta."""
    r = api_client.post("/api/v1/pedidos", json=_PEDIDO_PAYLOAD, headers=auth_headers)
    assert r.status_code == 201, r.text
    return r.json()


# --- GET /api/v1/me/dados (exportação / direito de acesso) ---


def test_get_me_dados_sem_auth_retorna_401(api_client: TestClient) -> None:
    """GET /me/dados sem Bearer retorna 401."""
    r = api_client.get("/api/v1/me/dados")
    assert r.status_code == 401


def test_get_me_dados_retorna_perfil_pedidos_e_atendimentos(
    api_client: TestClient, auth_headers: dict, usuario_autenticado: dict
) -> None:
    """GET /me/dados retorna o perfil, os pedidos (com contato) e os atendimentos."""
    pedido = _criar_pedido(api_client, auth_headers)

    r = api_client.get("/api/v1/me/dados", headers=auth_headers)

    assert r.status_code == 200, r.text
    body = r.json()

    # Perfil (UsuarioRead)
    assert body["perfil"]["id"] == usuario_autenticado["id"]
    assert body["perfil"]["email"] == usuario_autenticado["email"]
    assert "senha_hash" not in body["perfil"]

    # Pedidos do usuário, incluindo o próprio contato.
    assert len(body["pedidos"]) == 1
    assert body["pedidos"][0]["id"] == pedido["id"]
    assert body["pedidos"][0]["contato"] == _PEDIDO_PAYLOAD["contato"]

    # Sem atendimentos ainda.
    assert body["atendimentos"] == []


def test_get_me_dados_inclui_atendimentos_do_usuario(
    api_client: TestClient,
    auth_headers: dict,
    auth_headers_outro: dict,
) -> None:
    """GET /me/dados lista os atendimentos registrados pelo próprio usuário."""
    pedido = _criar_pedido(api_client, auth_headers)

    # O "outro" usuário registra um atendimento no pedido.
    atendimento = api_client.post(
        f"/api/v1/pedidos/{pedido['id']}/atendimentos",
        json={"tipo_ajuda": "Transporte", "observacao": "Posso levar ao vet."},
        headers=auth_headers_outro,
    )
    assert atendimento.status_code == 201, atendimento.text

    r = api_client.get("/api/v1/me/dados", headers=auth_headers_outro)

    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["atendimentos"]) == 1
    assert body["atendimentos"][0]["pedido_id"] == pedido["id"]
    assert body["atendimentos"][0]["tipo_ajuda"] == "Transporte"
    # O autor do pedido não registrou atendimentos.
    autor = api_client.get("/api/v1/me/dados", headers=auth_headers).json()
    assert autor["atendimentos"] == []


# --- DELETE /api/v1/me (exclusão / direito de eliminação) ---


def test_delete_me_sem_auth_retorna_401(api_client: TestClient) -> None:
    """DELETE /me sem Bearer retorna 401."""
    r = api_client.delete("/api/v1/me")
    assert r.status_code == 401


def test_delete_me_anonimiza_usuario_e_invalida_token(
    api_client: TestClient,
    auth_headers: dict,
    usuario_autenticado: dict,
    db_session: Session,
) -> None:
    """DELETE /me anonimiza o usuário, soft-deleta, e o token deixa de autenticar."""
    pedido = _criar_pedido(api_client, auth_headers)
    usuario_id = usuario_autenticado["id"]

    r = api_client.delete("/api/v1/me", headers=auth_headers)
    assert r.status_code == 204, r.text

    # O token não autentica mais (usuário soft-deletado -> 401).
    assert api_client.get("/api/v1/auth/me", headers=auth_headers).status_code == 401
    assert api_client.get("/api/v1/me/dados", headers=auth_headers).status_code == 401

    # Estado anonimizado no banco.
    db_session.expire_all()
    usuario = db_session.get(Usuario, usuario_id)
    assert usuario is not None
    assert usuario.deleted_at is not None
    assert usuario.nome == "Usuário removido"
    assert usuario.email == f"removido+{usuario_id}@anonimizado.local"
    assert usuario.telefone is None
    # A senha original não autentica mais.
    login = api_client.post(
        "/api/v1/auth/login",
        json={"email": "teste@example.com", "senha": "senha-de-teste-123"},
    )
    assert login.status_code == 401

    # O pedido do usuário foi soft-deletado e o contato anonimizado.
    db_session.expire_all()
    assert api_client.get(f"/api/v1/pedidos/{pedido['id']}").status_code == 404
    from app.models.pedido import PedidoAjuda

    pedido_db = db_session.get(PedidoAjuda, pedido["id"])
    assert pedido_db.deleted_at is not None
    assert pedido_db.contato != _PEDIDO_PAYLOAD["contato"]


def test_delete_me_libera_reuso_do_email_original(
    api_client: TestClient, auth_headers: dict
) -> None:
    """Após anonimizar, o e-mail original fica livre para um novo cadastro."""
    assert api_client.delete("/api/v1/me", headers=auth_headers).status_code == 204

    novo = api_client.post(
        "/api/v1/auth/registro",
        json={
            "nome": "Outra Pessoa",
            "email": "teste@example.com",
            "senha": "nova-senha-valida-123",
            "consentimento_aceito": True,
        },
    )
    assert novo.status_code == 201, novo.text


# --- DELETE /api/v1/admin/usuarios/{id} (exclusão por admin) ---


def test_admin_remove_usuario_terceiro(
    api_client: TestClient,
    auth_headers: dict,
    usuario_autenticado: dict,
    admin_headers: dict,
    db_session: Session,
) -> None:
    """Admin remove/anonimiza um usuário terceiro por id (204)."""
    pedido = _criar_pedido(api_client, auth_headers)
    usuario_id = usuario_autenticado["id"]

    r = api_client.delete(f"/api/v1/admin/usuarios/{usuario_id}", headers=admin_headers)
    assert r.status_code == 204, r.text

    # O token do usuário removido deixa de autenticar.
    assert api_client.get("/api/v1/auth/me", headers=auth_headers).status_code == 401

    db_session.expire_all()
    usuario = db_session.get(Usuario, usuario_id)
    assert usuario.deleted_at is not None
    assert usuario.email == f"removido+{usuario_id}@anonimizado.local"

    # O pedido do usuário removido foi soft-deletado.
    assert api_client.get(f"/api/v1/pedidos/{pedido['id']}").status_code == 404


def test_admin_remove_usuario_inexistente_retorna_404(
    api_client: TestClient, admin_headers: dict
) -> None:
    """DELETE admin de usuário inexistente retorna 404."""
    r = api_client.delete("/api/v1/admin/usuarios/9999", headers=admin_headers)
    assert r.status_code == 404
    assert r.json()["title"] == "Usuário não encontrado"


def test_admin_remove_usuario_sem_auth_retorna_401(
    api_client: TestClient, usuario_autenticado: dict
) -> None:
    """DELETE admin de usuário sem Bearer retorna 401."""
    r = api_client.delete(f"/api/v1/admin/usuarios/{usuario_autenticado['id']}")
    assert r.status_code == 401


def test_admin_remove_usuario_por_nao_admin_retorna_403(
    api_client: TestClient, auth_headers: dict, auth_headers_outro: dict, usuario_autenticado: dict
) -> None:
    """DELETE admin de usuário por usuário comum retorna 403."""
    r = api_client.delete(
        f"/api/v1/admin/usuarios/{usuario_autenticado['id']}", headers=auth_headers_outro
    )
    assert r.status_code == 403
    assert r.json()["title"] == "Acesso negado"
