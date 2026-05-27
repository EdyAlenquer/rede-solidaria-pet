"""Testes de integração da Fase 4 para doadores e atendimentos."""

from fastapi.testclient import TestClient

_PEDIDO_PAYLOAD = {
    "titulo": "Cãozinho ferido",
    "descricao": "Encontrado na rua X, precisa de atendimento veterinário.",
    "categoria": "resgate",
    "urgencia": "alta",
    "contato": "11999990000",
}

_DOADOR_PAYLOAD = {
    "nome": "Maria Silva",
    "telefone": "11988887777",
    "email": "maria@example.com",
}


def _criar_pedido(api_client: TestClient) -> dict:
    """Cria um pedido válido pela API de teste.

    Args:
        api_client: cliente HTTP com banco isolado.

    Returns:
        Corpo JSON do pedido criado.
    """
    response = api_client.post("/api/v1/pedidos", json=_PEDIDO_PAYLOAD)
    assert response.status_code == 201
    return response.json()


def _criar_doador(api_client: TestClient) -> dict:
    """Cria um doador válido pela API de teste.

    Args:
        api_client: cliente HTTP com banco isolado.

    Returns:
        Corpo JSON do doador criado.
    """
    response = api_client.post("/api/v1/doadores", json=_DOADOR_PAYLOAD)
    assert response.status_code == 201
    return response.json()


def test_post_doadores_cria_retorna_201_contato_completo_e_location(
    api_client: TestClient,
) -> None:
    """POST /api/v1/doadores cria doador administrativo com contato completo."""
    response = api_client.post("/api/v1/doadores", json=_DOADOR_PAYLOAD)

    assert response.status_code == 201
    body = response.json()
    assert body["id"] >= 1
    assert body["nome"] == _DOADOR_PAYLOAD["nome"]
    assert body["telefone"] == _DOADOR_PAYLOAD["telefone"]
    assert body["email"] == _DOADOR_PAYLOAD["email"]
    assert response.headers["location"] == f"/api/v1/doadores/{body['id']}"


def test_get_doador_por_id_retorna_contato_completo_administrativo(
    api_client: TestClient,
) -> None:
    """GET /api/v1/doadores/{id} retorna contato completo para uso administrativo."""
    doador = _criar_doador(api_client)

    response = api_client.get(f"/api/v1/doadores/{doador['id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == doador["id"]
    assert body["nome"] == _DOADOR_PAYLOAD["nome"]
    assert body["telefone"] == _DOADOR_PAYLOAD["telefone"]
    assert body["email"] == _DOADOR_PAYLOAD["email"]


def test_get_doadores_retorna_405_sem_listagem_publica(api_client: TestClient) -> None:
    """GET /api/v1/doadores não expõe listagem pública."""
    response = api_client.get("/api/v1/doadores")

    assert response.status_code == 405


def test_post_atendimentos_cria_sem_contato_e_altera_pedido_para_em_andamento(
    api_client: TestClient,
) -> None:
    """POST /api/v1/pedidos/{id}/atendimentos cria atendimento público sem contato."""
    pedido = _criar_pedido(api_client)
    doador = _criar_doador(api_client)

    response = api_client.post(
        f"/api/v1/pedidos/{pedido['id']}/atendimentos",
        json={
            "doador_id": doador["id"],
            "tipo_ajuda": "transporte",
            "observacao": "Posso levar ao veterinário.",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] >= 1
    assert body["pedido_id"] == pedido["id"]
    assert "doador_id" not in body
    assert "telefone" not in body
    assert "email" not in body

    pedido_response = api_client.get(f"/api/v1/pedidos/{pedido['id']}")
    assert pedido_response.status_code == 200
    assert pedido_response.json()["status"] == "em_andamento"


def test_get_atendimentos_lista_sem_telefone_ou_email(api_client: TestClient) -> None:
    """GET /api/v1/pedidos/{id}/atendimentos lista atendimentos sem contato privado."""
    pedido = _criar_pedido(api_client)
    doador = _criar_doador(api_client)
    api_client.post(
        f"/api/v1/pedidos/{pedido['id']}/atendimentos",
        json={
            "doador_id": doador["id"],
            "tipo_ajuda": "ração",
            "observacao": "Entrega no sábado.",
        },
    )

    response = api_client.get(f"/api/v1/pedidos/{pedido['id']}/atendimentos")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["pedido_id"] == pedido["id"]
    assert "doador_id" not in body[0]
    assert "telefone" not in body[0]
    assert "email" not in body[0]


def test_post_atendimento_em_pedido_concluido_retorna_409(
    api_client: TestClient,
) -> None:
    """POST atendimento em pedido concluído retorna conflito de pedido não atendível."""
    pedido = _criar_pedido(api_client)
    doador = _criar_doador(api_client)
    api_client.patch(f"/api/v1/pedidos/{pedido['id']}/status", json={"status": "concluido"})

    response = api_client.post(
        f"/api/v1/pedidos/{pedido['id']}/atendimentos",
        json={
            "doador_id": doador["id"],
            "tipo_ajuda": "lar temporário",
            "observacao": None,
        },
    )

    assert response.status_code == 409
    assert response.json()["title"] == "Pedido não pode receber atendimento"
