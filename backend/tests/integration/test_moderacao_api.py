"""Testes de integração da moderação: denúncias e rotas administrativas."""

from fastapi.testclient import TestClient

_PEDIDO_PAYLOAD = {
    "titulo": "Cãozinho ferido",
    "descricao": "Encontrado na rua X, precisa de atendimento veterinário.",
    "categoria": "resgate",
    "urgencia": "alta",
    "contato": "11999990000",
    "cidade": "São Paulo",
    "estado": "SP",
    "consentimento_aceito": True,
}


def _criar_pedido(api_client: TestClient, auth_headers: dict) -> dict:
    """Cria um pedido válido e retorna o corpo da resposta."""
    r = api_client.post("/api/v1/pedidos", json=_PEDIDO_PAYLOAD, headers=auth_headers)
    assert r.status_code == 201, r.text
    return r.json()


# --- Denúncias (POST autenticado) ---


def test_post_denuncia_autenticado_cria_201(
    api_client: TestClient, auth_headers: dict, auth_headers_outro: dict
) -> None:
    """POST /api/v1/pedidos/{id}/denuncias autenticado cria a denúncia."""
    pedido = _criar_pedido(api_client, auth_headers)

    r = api_client.post(
        f"/api/v1/pedidos/{pedido['id']}/denuncias",
        json={"motivo": "spam", "descricao": "Parece propaganda."},
        headers=auth_headers_outro,
    )

    assert r.status_code == 201
    body = r.json()
    assert body["pedido_id"] == pedido["id"]
    assert body["motivo"] == "spam"
    assert body["status"] == "aberta"


def test_post_denuncia_sem_auth_retorna_401(api_client: TestClient, auth_headers: dict) -> None:
    """POST denúncia sem Bearer retorna 401."""
    pedido = _criar_pedido(api_client, auth_headers)

    r = api_client.post(f"/api/v1/pedidos/{pedido['id']}/denuncias", json={"motivo": "golpe"})

    assert r.status_code == 401


def test_post_denuncia_pedido_inexistente_retorna_404(
    api_client: TestClient, auth_headers: dict
) -> None:
    """POST denúncia para pedido inexistente retorna 404."""
    r = api_client.post(
        "/api/v1/pedidos/9999/denuncias", json={"motivo": "outro"}, headers=auth_headers
    )

    assert r.status_code == 404
    assert r.json()["title"] == "Pedido não encontrado"


def test_post_denuncia_motivo_invalido_retorna_422(
    api_client: TestClient, auth_headers: dict
) -> None:
    """POST denúncia com motivo fora do enum retorna 422."""
    pedido = _criar_pedido(api_client, auth_headers)

    r = api_client.post(
        f"/api/v1/pedidos/{pedido['id']}/denuncias",
        json={"motivo": "inexistente"},
        headers=auth_headers,
    )

    assert r.status_code == 422


# --- Rotas administrativas ---


def test_admin_lista_denuncias(
    api_client: TestClient, auth_headers: dict, admin_headers: dict
) -> None:
    """GET /api/v1/admin/denuncias lista as denúncias (admin)."""
    pedido = _criar_pedido(api_client, auth_headers)
    api_client.post(
        f"/api/v1/pedidos/{pedido['id']}/denuncias",
        json={"motivo": "spam"},
        headers=auth_headers,
    )

    r = api_client.get("/api/v1/admin/denuncias", headers=admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert len(body) == 1
    assert body[0]["pedido_id"] == pedido["id"]


def test_admin_lista_denuncias_sem_auth_retorna_401(api_client: TestClient) -> None:
    """GET /api/v1/admin/denuncias sem Bearer retorna 401."""
    r = api_client.get("/api/v1/admin/denuncias")
    assert r.status_code == 401


def test_admin_lista_denuncias_por_nao_admin_retorna_403(
    api_client: TestClient, auth_headers: dict
) -> None:
    """GET /api/v1/admin/denuncias por usuário comum retorna 403."""
    r = api_client.get("/api/v1/admin/denuncias", headers=auth_headers)
    assert r.status_code == 403
    assert r.json()["title"] == "Acesso negado"


def test_admin_ocultar_e_reexibir_pedido(
    api_client: TestClient, auth_headers: dict, admin_headers: dict
) -> None:
    """Admin oculta o pedido (some do público) e depois reexibe (volta)."""
    pedido = _criar_pedido(api_client, auth_headers)

    ocultar = api_client.patch(
        f"/api/v1/admin/pedidos/{pedido['id']}/ocultar", headers=admin_headers
    )
    assert ocultar.status_code == 200
    assert ocultar.json()["oculto"] is True
    # Some das leituras públicas.
    assert api_client.get(f"/api/v1/pedidos/{pedido['id']}").status_code == 404
    assert api_client.get("/api/v1/pedidos").json()["page_info"]["total"] == 0

    reexibir = api_client.patch(
        f"/api/v1/admin/pedidos/{pedido['id']}/reexibir", headers=admin_headers
    )
    assert reexibir.status_code == 200
    assert reexibir.json()["oculto"] is False
    assert api_client.get(f"/api/v1/pedidos/{pedido['id']}").status_code == 200


def test_revelar_contato_de_pedido_oculto_retorna_404(
    api_client: TestClient, auth_headers: dict, admin_headers: dict
) -> None:
    """Pedido ocultado pela moderação não vaza o contato no endpoint /contato.

    Regressão de segurança: `revelar_contato_pedido` deve usar a mesma semântica
    pública do detalhe (404 para ocultos), e não expor o contato de um pedido que
    a moderação tornou invisível.
    """
    pedido = _criar_pedido(api_client, auth_headers)

    ocultar = api_client.patch(
        f"/api/v1/admin/pedidos/{pedido['id']}/ocultar", headers=admin_headers
    )
    assert ocultar.status_code == 200

    r = api_client.get(f"/api/v1/pedidos/{pedido['id']}/contato", headers=auth_headers)

    assert r.status_code == 404


def test_revelar_contato_de_pedido_visivel_retorna_contato(
    api_client: TestClient, auth_headers: dict
) -> None:
    """O caminho normal (pedido visível) continua revelando o contato ao logado."""
    pedido = _criar_pedido(api_client, auth_headers)

    r = api_client.get(f"/api/v1/pedidos/{pedido['id']}/contato", headers=auth_headers)

    assert r.status_code == 200
    assert r.json()["contato"] == _PEDIDO_PAYLOAD["contato"]


def test_admin_ocultar_por_nao_admin_retorna_403(
    api_client: TestClient, auth_headers: dict
) -> None:
    """PATCH ocultar por usuário comum retorna 403."""
    pedido = _criar_pedido(api_client, auth_headers)

    r = api_client.patch(f"/api/v1/admin/pedidos/{pedido['id']}/ocultar", headers=auth_headers)

    assert r.status_code == 403


def test_admin_ocultar_pedido_inexistente_retorna_404(
    api_client: TestClient, admin_headers: dict
) -> None:
    """PATCH ocultar pedido inexistente retorna 404."""
    r = api_client.patch("/api/v1/admin/pedidos/9999/ocultar", headers=admin_headers)
    assert r.status_code == 404


def test_admin_resolver_denuncia(
    api_client: TestClient, auth_headers: dict, admin_headers: dict
) -> None:
    """PATCH /api/v1/admin/denuncias/{id}/resolver marca como resolvida."""
    pedido = _criar_pedido(api_client, auth_headers)
    denuncia = api_client.post(
        f"/api/v1/pedidos/{pedido['id']}/denuncias",
        json={"motivo": "conteudo_improprio"},
        headers=auth_headers,
    ).json()

    r = api_client.patch(
        f"/api/v1/admin/denuncias/{denuncia['id']}/resolver", headers=admin_headers
    )

    assert r.status_code == 200
    assert r.json()["status"] == "resolvida"


def test_admin_resolver_denuncia_inexistente_retorna_404(
    api_client: TestClient, admin_headers: dict
) -> None:
    """PATCH resolver denúncia inexistente retorna 404."""
    r = api_client.patch("/api/v1/admin/denuncias/9999/resolver", headers=admin_headers)
    assert r.status_code == 404
