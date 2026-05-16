"""Testes de integração dos endpoints REST de pedidos."""

from fastapi.testclient import TestClient

_VALID_PAYLOAD = {
    "titulo": "Cãozinho ferido",
    "descricao": "Encontrado na rua X, precisa de atendimento veterinário.",
    "categoria": "resgate",
    "urgencia": "alta",
    "contato": "11999990000",
}


def test_post_pedidos_cria_e_retorna_201_com_location(api_client: TestClient) -> None:
    """POST /api/v1/pedidos cria o pedido, retorna 201 e header Location."""
    r = api_client.post("/api/v1/pedidos", json=_VALID_PAYLOAD)

    assert r.status_code == 201
    body = r.json()
    assert body["titulo"] == "Cãozinho ferido"
    assert body["status"] == "aberto"
    assert body["id"] >= 1
    assert r.headers["location"] == f"/api/v1/pedidos/{body['id']}"


def test_post_pedidos_rejeita_payload_invalido_com_422_problem_json(
    api_client: TestClient,
) -> None:
    """Falha de validação retorna 422 com ProblemDetail."""
    payload = {**_VALID_PAYLOAD, "titulo": "x"}  # titulo curto
    r = api_client.post("/api/v1/pedidos", json=payload)

    assert r.status_code == 422
    assert r.headers["content-type"] == "application/problem+json"
    assert r.json()["title"] == "Erro de validação"


def test_get_pedidos_lista_paginada(api_client: TestClient) -> None:
    """GET /api/v1/pedidos retorna items + page_info."""
    for i in range(3):
        api_client.post("/api/v1/pedidos", json={**_VALID_PAYLOAD, "titulo": f"Pedido {i}"})

    r = api_client.get("/api/v1/pedidos?page=1&page_size=2")

    assert r.status_code == 200
    body = r.json()
    assert len(body["items"]) == 2
    assert body["page_info"]["page"] == 1
    assert body["page_info"]["page_size"] == 2
    assert body["page_info"]["total"] == 3
    assert body["page_info"]["total_pages"] == 2


def test_get_pedidos_filtra_por_status_urgencia_e_q(api_client: TestClient) -> None:
    """Filtros combinados na listagem retornam o subconjunto correto."""
    api_client.post(
        "/api/v1/pedidos",
        json={**_VALID_PAYLOAD, "titulo": "Cãozinho ferido", "urgencia": "alta"},
    )
    api_client.post(
        "/api/v1/pedidos",
        json={**_VALID_PAYLOAD, "titulo": "Gata grávida", "urgencia": "baixa"},
    )

    r = api_client.get("/api/v1/pedidos?urgencia=alta&q=cãozinho")

    assert r.status_code == 200
    body = r.json()
    assert body["page_info"]["total"] == 1
    assert body["items"][0]["titulo"] == "Cãozinho ferido"


def test_get_pedido_por_id_retorna_detalhe(api_client: TestClient) -> None:
    """GET /api/v1/pedidos/{id} retorna o detalhe com contato."""
    criado = api_client.post("/api/v1/pedidos", json=_VALID_PAYLOAD).json()

    r = api_client.get(f"/api/v1/pedidos/{criado['id']}")

    assert r.status_code == 200
    body = r.json()
    assert body["id"] == criado["id"]
    assert body["contato"] == _VALID_PAYLOAD["contato"]


def test_get_pedido_inexistente_retorna_404_problem_json(api_client: TestClient) -> None:
    """GET /api/v1/pedidos/{id} para id inexistente retorna 404 ProblemDetail."""
    r = api_client.get("/api/v1/pedidos/9999")

    assert r.status_code == 404
    assert r.headers["content-type"] == "application/problem+json"
    body = r.json()
    assert body["title"] == "Pedido não encontrado"
    assert body["status"] == 404


def test_patch_status_transicao_valida(api_client: TestClient) -> None:
    """PATCH /api/v1/pedidos/{id}/status com transição válida retorna 200."""
    criado = api_client.post("/api/v1/pedidos", json=_VALID_PAYLOAD).json()

    r = api_client.patch(f"/api/v1/pedidos/{criado['id']}/status", json={"status": "em_andamento"})

    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "em_andamento"


def test_patch_status_idempotente(api_client: TestClient) -> None:
    """PATCH com o mesmo status atual retorna 200 sem erro."""
    criado = api_client.post("/api/v1/pedidos", json=_VALID_PAYLOAD).json()

    r = api_client.patch(f"/api/v1/pedidos/{criado['id']}/status", json={"status": "aberto"})

    assert r.status_code == 200
    assert r.json()["status"] == "aberto"


def test_patch_status_transicao_invalida_retorna_409(api_client: TestClient) -> None:
    """Transição em_andamento -> aberto retorna 409 ProblemDetail."""
    criado = api_client.post("/api/v1/pedidos", json=_VALID_PAYLOAD).json()
    api_client.patch(f"/api/v1/pedidos/{criado['id']}/status", json={"status": "em_andamento"})

    r = api_client.patch(f"/api/v1/pedidos/{criado['id']}/status", json={"status": "aberto"})

    assert r.status_code == 409
    assert r.headers["content-type"] == "application/problem+json"
    body = r.json()
    assert body["title"] == "Transição de status inválida"


def test_patch_status_concluido_e_terminal(api_client: TestClient) -> None:
    """Pedido concluído não aceita mudança para outro status."""
    criado = api_client.post("/api/v1/pedidos", json=_VALID_PAYLOAD).json()
    api_client.patch(f"/api/v1/pedidos/{criado['id']}/status", json={"status": "concluido"})

    r = api_client.patch(f"/api/v1/pedidos/{criado['id']}/status", json={"status": "em_andamento"})

    assert r.status_code == 409


def test_patch_status_pedido_inexistente_retorna_404(api_client: TestClient) -> None:
    """PATCH em pedido inexistente retorna 404 ProblemDetail."""
    r = api_client.patch("/api/v1/pedidos/9999/status", json={"status": "em_andamento"})

    assert r.status_code == 404
    body = r.json()
    assert body["title"] == "Pedido não encontrado"


def test_patch_status_payload_invalido_retorna_422(api_client: TestClient) -> None:
    """PATCH com status fora do enum retorna 422 ProblemDetail."""
    criado = api_client.post("/api/v1/pedidos", json=_VALID_PAYLOAD).json()

    r = api_client.patch(f"/api/v1/pedidos/{criado['id']}/status", json={"status": "cancelado"})

    assert r.status_code == 422
    assert r.json()["title"] == "Erro de validação"
