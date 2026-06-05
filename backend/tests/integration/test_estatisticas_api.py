"""Testes de integração do endpoint público de estatísticas."""

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


def test_estatisticas_sem_dados_retorna_zeros(api_client: TestClient) -> None:
    """GET /api/v1/estatisticas sem dados retorna todos os contadores em zero."""
    r = api_client.get("/api/v1/estatisticas")

    assert r.status_code == 200
    assert r.json() == {
        "total_pedidos": 0,
        "pedidos_abertos": 0,
        "pedidos_concluidos": 0,
        "total_atendimentos": 0,
        "total_cidades": 0,
    }


def test_estatisticas_eh_publico_sem_auth(api_client: TestClient) -> None:
    """GET /api/v1/estatisticas é público (não exige autenticação)."""
    r = api_client.get("/api/v1/estatisticas")
    assert r.status_code == 200


def test_estatisticas_tem_cache_control_curto(api_client: TestClient) -> None:
    """GET /api/v1/estatisticas (público) envia Cache-Control curto e compartilhável."""
    r = api_client.get("/api/v1/estatisticas")

    assert r.status_code == 200
    assert r.headers["cache-control"] == "public, max-age=30"


def test_estatisticas_conta_pedidos_status_cidades_e_atendimentos(
    api_client: TestClient, auth_headers: dict, auth_headers_outro: dict
) -> None:
    """Os contadores refletem pedidos, status, cidades distintas e atendimentos."""
    # Pedido 1 (SP) — será concluído e receberá um atendimento.
    p1 = api_client.post("/api/v1/pedidos", json=_PEDIDO_PAYLOAD, headers=auth_headers).json()
    # Pedido 2 (RJ) — permanece aberto.
    api_client.post(
        "/api/v1/pedidos",
        json={**_PEDIDO_PAYLOAD, "cidade": "Rio de Janeiro", "estado": "RJ"},
        headers=auth_headers,
    )
    # Pedido 3 (SP de novo) — cidade repetida, não conta duas vezes.
    api_client.post("/api/v1/pedidos", json=_PEDIDO_PAYLOAD, headers=auth_headers)

    # Atendimento por outro usuário move p1 para em_andamento; depois concluímos.
    api_client.post(
        f"/api/v1/pedidos/{p1['id']}/atendimentos",
        json={"tipo_ajuda": "transporte"},
        headers=auth_headers_outro,
    )
    api_client.patch(
        f"/api/v1/pedidos/{p1['id']}/status",
        json={"status": "concluido"},
        headers=auth_headers,
    )

    r = api_client.get("/api/v1/estatisticas")

    assert r.status_code == 200
    body = r.json()
    assert body["total_pedidos"] == 3
    assert body["pedidos_abertos"] == 2
    assert body["pedidos_concluidos"] == 1
    assert body["total_atendimentos"] == 1
    assert body["total_cidades"] == 2


def test_estatisticas_ignora_soft_deleted_e_ocultos(
    api_client: TestClient, auth_headers: dict, admin_headers: dict
) -> None:
    """Pedidos soft-deletados e ocultos não entram nas estatísticas."""
    visivel = api_client.post("/api/v1/pedidos", json=_PEDIDO_PAYLOAD, headers=auth_headers).json()
    removido = api_client.post(
        "/api/v1/pedidos",
        json={**_PEDIDO_PAYLOAD, "cidade": "Curitiba", "estado": "PR"},
        headers=auth_headers,
    ).json()
    oculto = api_client.post(
        "/api/v1/pedidos",
        json={**_PEDIDO_PAYLOAD, "cidade": "Salvador", "estado": "BA"},
        headers=auth_headers,
    ).json()

    api_client.delete(f"/api/v1/pedidos/{removido['id']}", headers=auth_headers)
    api_client.patch(f"/api/v1/admin/pedidos/{oculto['id']}/ocultar", headers=admin_headers)

    r = api_client.get("/api/v1/estatisticas")

    assert r.status_code == 200
    body = r.json()
    assert body["total_pedidos"] == 1
    assert body["pedidos_abertos"] == 1
    assert body["total_cidades"] == 1
    # Apenas o pedido visível deve permanecer contabilizado.
    assert visivel["id"]
