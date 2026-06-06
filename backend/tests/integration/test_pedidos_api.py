"""Testes de integração dos endpoints REST de pedidos."""

from fastapi.testclient import TestClient

_VALID_PAYLOAD = {
    "titulo": "Cãozinho ferido",
    "descricao": "Encontrado na rua X, precisa de atendimento veterinário.",
    "categoria": "resgate",
    "urgencia": "alta",
    "contato": "11999990000",
    "cidade": "São Paulo",
    "estado": "SP",
    "consentimento_aceito": True,
}


def test_post_pedidos_cria_e_retorna_201_com_location(
    api_client: TestClient, auth_headers: dict
) -> None:
    """POST /api/v1/pedidos cria o pedido, retorna 201 e header Location."""
    r = api_client.post("/api/v1/pedidos", json=_VALID_PAYLOAD, headers=auth_headers)

    assert r.status_code == 201
    body = r.json()
    assert body["titulo"] == "Cãozinho ferido"
    assert body["status"] == "aberto"
    assert body["id"] >= 1
    assert r.headers["location"] == f"/api/v1/pedidos/{body['id']}"


def test_post_pedidos_sem_auth_retorna_401(api_client: TestClient) -> None:
    """POST /api/v1/pedidos sem Bearer retorna 401 (autenticação obrigatória)."""
    r = api_client.post("/api/v1/pedidos", json=_VALID_PAYLOAD)

    assert r.status_code == 401
    assert r.headers["content-type"] == "application/problem+json"


def test_post_pedidos_vincula_autor_ao_usuario_autenticado(
    api_client: TestClient,
    db_session,
    auth_headers: dict,
    usuario_autenticado: dict,
) -> None:
    """O pedido criado fica vinculado ao usuário autenticado (autor_id)."""
    from app.models.pedido import PedidoAjuda

    r = api_client.post("/api/v1/pedidos", json=_VALID_PAYLOAD, headers=auth_headers)

    assert r.status_code == 201
    pedido_id = r.json()["id"]

    pedido = db_session.get(PedidoAjuda, pedido_id)
    assert pedido.autor_id == usuario_autenticado["id"]


def test_post_pedidos_rejeita_payload_invalido_com_422_problem_json(
    api_client: TestClient, auth_headers: dict
) -> None:
    """Falha de validação retorna 422 com ProblemDetail."""
    payload = {**_VALID_PAYLOAD, "titulo": "x"}  # titulo curto
    r = api_client.post("/api/v1/pedidos", json=payload, headers=auth_headers)

    assert r.status_code == 422
    assert r.headers["content-type"] == "application/problem+json"
    assert r.json()["title"] == "Erro de validação"


def test_get_pedidos_lista_paginada(api_client: TestClient, auth_headers: dict) -> None:
    """GET /api/v1/pedidos retorna items + page_info."""
    for i in range(3):
        api_client.post(
            "/api/v1/pedidos",
            json={**_VALID_PAYLOAD, "titulo": f"Pedido {i}"},
            headers=auth_headers,
        )

    r = api_client.get("/api/v1/pedidos?page=1&page_size=2")

    assert r.status_code == 200
    body = r.json()
    assert len(body["items"]) == 2
    assert body["page_info"]["page"] == 1
    assert body["page_info"]["page_size"] == 2
    assert body["page_info"]["total"] == 3
    assert body["page_info"]["total_pages"] == 2


def test_get_pedidos_filtra_por_status_urgencia_e_q(
    api_client: TestClient, auth_headers: dict
) -> None:
    """Filtros combinados na listagem retornam o subconjunto correto."""
    api_client.post(
        "/api/v1/pedidos",
        json={**_VALID_PAYLOAD, "titulo": "Cãozinho ferido", "urgencia": "alta"},
        headers=auth_headers,
    )
    api_client.post(
        "/api/v1/pedidos",
        json={**_VALID_PAYLOAD, "titulo": "Gata grávida", "urgencia": "baixa"},
        headers=auth_headers,
    )

    r = api_client.get("/api/v1/pedidos?urgencia=alta&q=cãozinho")

    assert r.status_code == 200
    body = r.json()
    assert body["page_info"]["total"] == 1
    assert body["items"][0]["titulo"] == "Cãozinho ferido"


def test_get_pedidos_filtra_por_categoria(api_client: TestClient, auth_headers: dict) -> None:
    """Filtro `categoria` na listagem retorna apenas a categoria pedida."""
    api_client.post(
        "/api/v1/pedidos",
        json={**_VALID_PAYLOAD, "titulo": "Resgate urgente", "categoria": "resgate"},
        headers=auth_headers,
    )
    api_client.post(
        "/api/v1/pedidos",
        json={**_VALID_PAYLOAD, "titulo": "Leva ao vet", "categoria": "veterinario"},
        headers=auth_headers,
    )

    r = api_client.get("/api/v1/pedidos?categoria=veterinario")

    assert r.status_code == 200
    body = r.json()
    assert body["page_info"]["total"] == 1
    assert body["items"][0]["titulo"] == "Leva ao vet"


def test_post_pedido_sem_consentimento_retorna_422(
    api_client: TestClient, auth_headers: dict
) -> None:
    """POST sem aceitar o consentimento retorna 422 ProblemDetail."""
    payload = {**_VALID_PAYLOAD, "consentimento_aceito": False}
    r = api_client.post("/api/v1/pedidos", json=payload, headers=auth_headers)

    assert r.status_code == 422
    assert r.json()["title"] == "Erro de validação"


def test_post_pedido_rejeita_uf_invalida(api_client: TestClient, auth_headers: dict) -> None:
    """POST com UF fora do padrão de 2 letras retorna 422."""
    r = api_client.post(
        "/api/v1/pedidos", json={**_VALID_PAYLOAD, "estado": "São Paulo"}, headers=auth_headers
    )

    assert r.status_code == 422
    assert r.json()["title"] == "Erro de validação"


def test_get_pedido_inclui_localizacao_e_imagens_default(
    api_client: TestClient, auth_headers: dict
) -> None:
    """A leitura do pedido inclui cidade/estado e `imagens` (default vazia)."""
    criado = api_client.post("/api/v1/pedidos", json=_VALID_PAYLOAD, headers=auth_headers).json()

    body = api_client.get(f"/api/v1/pedidos/{criado['id']}").json()

    assert body["cidade"] == "São Paulo"
    assert body["estado"] == "SP"
    assert body["imagens"] == []


def test_get_pedidos_filtra_por_cidade_estado_especie_porte(
    api_client: TestClient, auth_headers: dict
) -> None:
    """Os novos query params filtram a listagem corretamente."""
    api_client.post(
        "/api/v1/pedidos",
        json={
            **_VALID_PAYLOAD,
            "titulo": "Cão médio SP",
            "cidade": "São Paulo",
            "estado": "SP",
            "especie": "cao",
            "porte": "medio",
        },
        headers=auth_headers,
    )
    api_client.post(
        "/api/v1/pedidos",
        json={
            **_VALID_PAYLOAD,
            "titulo": "Gato RJ",
            "cidade": "Rio de Janeiro",
            "estado": "RJ",
            "especie": "gato",
            "porte": "pequeno",
        },
        headers=auth_headers,
    )

    r = api_client.get("/api/v1/pedidos?cidade=São Paulo&estado=SP&especie=cao&porte=medio")

    assert r.status_code == 200
    body = r.json()
    assert body["page_info"]["total"] == 1
    assert body["items"][0]["titulo"] == "Cão médio SP"


def test_post_pedido_rejeita_categoria_fora_do_enum(
    api_client: TestClient, auth_headers: dict
) -> None:
    """Categoria fora do enum retorna 422 ProblemDetail."""
    r = api_client.post(
        "/api/v1/pedidos",
        json={**_VALID_PAYLOAD, "categoria": "categoria_invalida"},
        headers=auth_headers,
    )

    assert r.status_code == 422
    assert r.json()["title"] == "Erro de validação"


def test_data_criacao_serializa_com_offset_de_timezone(
    api_client: TestClient, auth_headers: dict
) -> None:
    """`data_criacao` na resposta carrega offset ISO-8601 (UTC)."""
    criado = api_client.post("/api/v1/pedidos", json=_VALID_PAYLOAD, headers=auth_headers).json()

    data_criacao = criado["data_criacao"]
    assert data_criacao.endswith("+00:00") or data_criacao.endswith("Z")


def test_get_pedido_por_id_retorna_detalhe_sem_contato(
    api_client: TestClient, auth_headers: dict
) -> None:
    """GET /api/v1/pedidos/{id} retorna o detalhe público SEM o campo contato."""
    criado = api_client.post("/api/v1/pedidos", json=_VALID_PAYLOAD, headers=auth_headers).json()

    r = api_client.get(f"/api/v1/pedidos/{criado['id']}")

    assert r.status_code == 200
    body = r.json()
    assert body["id"] == criado["id"]
    assert "contato" not in body


def test_get_pedido_por_id_inclui_autor_id(
    api_client: TestClient, auth_headers: dict, usuario_autenticado: dict
) -> None:
    """O detalhe público traz `autor_id` para o frontend decidir editar/excluir."""
    criado = api_client.post("/api/v1/pedidos", json=_VALID_PAYLOAD, headers=auth_headers).json()

    body = api_client.get(f"/api/v1/pedidos/{criado['id']}").json()

    assert body["autor_id"] == usuario_autenticado["id"]


def test_listagem_publica_inclui_autor_id(
    api_client: TestClient, auth_headers: dict, usuario_autenticado: dict
) -> None:
    """Os itens da listagem pública trazem `autor_id` (apenas o id, sem PII)."""
    api_client.post("/api/v1/pedidos", json=_VALID_PAYLOAD, headers=auth_headers)

    body = api_client.get("/api/v1/pedidos").json()

    assert body["items"]
    assert body["items"][0]["autor_id"] == usuario_autenticado["id"]


def test_listagem_publica_tem_cache_control_curto(
    api_client: TestClient, auth_headers: dict
) -> None:
    """GET /api/v1/pedidos (público) envia Cache-Control curto e compartilhável."""
    api_client.post("/api/v1/pedidos", json=_VALID_PAYLOAD, headers=auth_headers)

    r = api_client.get("/api/v1/pedidos")

    assert r.status_code == 200
    assert r.headers["cache-control"] == "public, max-age=30"


def test_rota_autenticada_nao_tem_cache_control_publico(
    api_client: TestClient, auth_headers: dict
) -> None:
    """Rotas autenticadas (ex.: revelar contato) não recebem Cache-Control público."""
    criado = api_client.post("/api/v1/pedidos", json=_VALID_PAYLOAD, headers=auth_headers).json()

    r = api_client.get(f"/api/v1/pedidos/{criado['id']}/contato", headers=auth_headers)

    assert r.status_code == 200
    assert r.headers.get("cache-control") != "public, max-age=30"


def test_listagem_publica_nao_expoe_contato(api_client: TestClient, auth_headers: dict) -> None:
    """GET /api/v1/pedidos (lista pública) não traz o campo contato nos itens."""
    api_client.post("/api/v1/pedidos", json=_VALID_PAYLOAD, headers=auth_headers)

    r = api_client.get("/api/v1/pedidos")

    assert r.status_code == 200
    body = r.json()
    assert body["items"]
    assert "contato" not in body["items"][0]


def test_get_contato_exige_auth(api_client: TestClient, auth_headers: dict) -> None:
    """GET /api/v1/pedidos/{id}/contato sem Bearer retorna 401."""
    criado = api_client.post("/api/v1/pedidos", json=_VALID_PAYLOAD, headers=auth_headers).json()

    r = api_client.get(f"/api/v1/pedidos/{criado['id']}/contato")

    assert r.status_code == 401
    assert r.headers["content-type"] == "application/problem+json"


def test_get_contato_autenticado_retorna_contato(
    api_client: TestClient, auth_headers: dict
) -> None:
    """GET /api/v1/pedidos/{id}/contato autenticado retorna contato e link wa.me."""
    criado = api_client.post("/api/v1/pedidos", json=_VALID_PAYLOAD, headers=auth_headers).json()

    r = api_client.get(f"/api/v1/pedidos/{criado['id']}/contato", headers=auth_headers)

    assert r.status_code == 200
    assert r.json() == {
        "contato": _VALID_PAYLOAD["contato"],
        "whatsapp": "https://wa.me/5511999990000",
    }


def test_get_contato_com_email_retorna_whatsapp_nulo(
    api_client: TestClient, auth_headers: dict
) -> None:
    """Quando o contato é um e-mail, `whatsapp` vem nulo (não é telefone)."""
    payload = {**_VALID_PAYLOAD, "contato": "protetor@example.com"}
    criado = api_client.post("/api/v1/pedidos", json=payload, headers=auth_headers).json()

    r = api_client.get(f"/api/v1/pedidos/{criado['id']}/contato", headers=auth_headers)

    assert r.status_code == 200
    assert r.json() == {"contato": "protetor@example.com", "whatsapp": None}


def test_get_contato_pedido_inexistente_retorna_404(
    api_client: TestClient, auth_headers: dict
) -> None:
    """GET /api/v1/pedidos/{id}/contato para id inexistente retorna 404."""
    r = api_client.get("/api/v1/pedidos/9999/contato", headers=auth_headers)

    assert r.status_code == 404
    assert r.json()["title"] == "Pedido não encontrado"


def test_get_pedido_inexistente_retorna_404_problem_json(api_client: TestClient) -> None:
    """GET /api/v1/pedidos/{id} para id inexistente retorna 404 ProblemDetail."""
    r = api_client.get("/api/v1/pedidos/9999")

    assert r.status_code == 404
    assert r.headers["content-type"] == "application/problem+json"
    body = r.json()
    assert body["title"] == "Pedido não encontrado"
    assert body["status"] == 404


def test_patch_status_transicao_valida(api_client: TestClient, auth_headers: dict) -> None:
    """PATCH /api/v1/pedidos/{id}/status com transição válida retorna 200."""
    criado = api_client.post("/api/v1/pedidos", json=_VALID_PAYLOAD, headers=auth_headers).json()

    r = api_client.patch(
        f"/api/v1/pedidos/{criado['id']}/status",
        json={"status": "em_andamento"},
        headers=auth_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "em_andamento"


def test_patch_status_sem_auth_retorna_401(api_client: TestClient, auth_headers: dict) -> None:
    """PATCH /status sem Bearer retorna 401 (autenticação obrigatória)."""
    criado = api_client.post("/api/v1/pedidos", json=_VALID_PAYLOAD, headers=auth_headers).json()

    r = api_client.patch(f"/api/v1/pedidos/{criado['id']}/status", json={"status": "em_andamento"})

    assert r.status_code == 401


def test_patch_status_por_nao_autor_retorna_403(
    api_client: TestClient, auth_headers: dict, auth_headers_outro: dict
) -> None:
    """PATCH /status por usuário que não é autor nem admin retorna 403."""
    criado = api_client.post("/api/v1/pedidos", json=_VALID_PAYLOAD, headers=auth_headers).json()

    r = api_client.patch(
        f"/api/v1/pedidos/{criado['id']}/status",
        json={"status": "em_andamento"},
        headers=auth_headers_outro,
    )

    assert r.status_code == 403
    assert r.json()["title"] == "Acesso negado"


def test_patch_status_por_admin_permitido(
    api_client: TestClient, auth_headers: dict, admin_headers: dict
) -> None:
    """Admin pode mudar o status de pedido de outro autor."""
    criado = api_client.post("/api/v1/pedidos", json=_VALID_PAYLOAD, headers=auth_headers).json()

    r = api_client.patch(
        f"/api/v1/pedidos/{criado['id']}/status",
        json={"status": "em_andamento"},
        headers=admin_headers,
    )

    assert r.status_code == 200
    assert r.json()["status"] == "em_andamento"


def test_patch_status_aberto_para_cancelado(api_client: TestClient, auth_headers: dict) -> None:
    """PATCH aberto -> cancelado é permitido e retorna 200."""
    criado = api_client.post("/api/v1/pedidos", json=_VALID_PAYLOAD, headers=auth_headers).json()

    r = api_client.patch(
        f"/api/v1/pedidos/{criado['id']}/status",
        json={"status": "cancelado"},
        headers=auth_headers,
    )

    assert r.status_code == 200
    assert r.json()["status"] == "cancelado"


def test_patch_status_cancelado_reabre_para_aberto(
    api_client: TestClient, auth_headers: dict
) -> None:
    """PATCH cancelado -> aberto (reabrir) é permitido e retorna 200."""
    criado = api_client.post("/api/v1/pedidos", json=_VALID_PAYLOAD, headers=auth_headers).json()
    api_client.patch(
        f"/api/v1/pedidos/{criado['id']}/status",
        json={"status": "cancelado"},
        headers=auth_headers,
    )

    r = api_client.patch(
        f"/api/v1/pedidos/{criado['id']}/status",
        json={"status": "aberto"},
        headers=auth_headers,
    )

    assert r.status_code == 200
    assert r.json()["status"] == "aberto"


def test_patch_status_idempotente(api_client: TestClient, auth_headers: dict) -> None:
    """PATCH com o mesmo status atual retorna 200 sem erro."""
    criado = api_client.post("/api/v1/pedidos", json=_VALID_PAYLOAD, headers=auth_headers).json()

    r = api_client.patch(
        f"/api/v1/pedidos/{criado['id']}/status",
        json={"status": "aberto"},
        headers=auth_headers,
    )

    assert r.status_code == 200
    assert r.json()["status"] == "aberto"


def test_patch_status_transicao_invalida_retorna_409(
    api_client: TestClient, auth_headers: dict
) -> None:
    """Transição aberto -> concluido (pulo direto) retorna 409 ProblemDetail."""
    criado = api_client.post("/api/v1/pedidos", json=_VALID_PAYLOAD, headers=auth_headers).json()

    r = api_client.patch(
        f"/api/v1/pedidos/{criado['id']}/status",
        json={"status": "concluido"},
        headers=auth_headers,
    )

    assert r.status_code == 409
    assert r.headers["content-type"] == "application/problem+json"
    body = r.json()
    assert body["title"] == "Transição de status inválida"


def test_patch_status_em_andamento_para_aberto_reabre(
    api_client: TestClient, auth_headers: dict
) -> None:
    """Transição em_andamento -> aberto (reabrir) é permitida e retorna 200."""
    criado = api_client.post("/api/v1/pedidos", json=_VALID_PAYLOAD, headers=auth_headers).json()
    api_client.patch(
        f"/api/v1/pedidos/{criado['id']}/status",
        json={"status": "em_andamento"},
        headers=auth_headers,
    )

    r = api_client.patch(
        f"/api/v1/pedidos/{criado['id']}/status",
        json={"status": "aberto"},
        headers=auth_headers,
    )

    assert r.status_code == 200
    assert r.json()["status"] == "aberto"


def test_patch_status_concluido_reabre_para_em_andamento(
    api_client: TestClient, auth_headers: dict
) -> None:
    """Pedido concluído pode ser reaberto para em_andamento (200)."""
    criado = api_client.post("/api/v1/pedidos", json=_VALID_PAYLOAD, headers=auth_headers).json()
    api_client.patch(
        f"/api/v1/pedidos/{criado['id']}/status",
        json={"status": "em_andamento"},
        headers=auth_headers,
    )
    api_client.patch(
        f"/api/v1/pedidos/{criado['id']}/status",
        json={"status": "concluido"},
        headers=auth_headers,
    )

    r = api_client.patch(
        f"/api/v1/pedidos/{criado['id']}/status",
        json={"status": "em_andamento"},
        headers=auth_headers,
    )

    assert r.status_code == 200
    assert r.json()["status"] == "em_andamento"


def test_patch_status_concluido_para_aberto_bloqueado(
    api_client: TestClient, auth_headers: dict
) -> None:
    """Concluído não pode ir direto para aberto — apenas reabrir via em_andamento."""
    criado = api_client.post("/api/v1/pedidos", json=_VALID_PAYLOAD, headers=auth_headers).json()
    api_client.patch(
        f"/api/v1/pedidos/{criado['id']}/status",
        json={"status": "em_andamento"},
        headers=auth_headers,
    )
    api_client.patch(
        f"/api/v1/pedidos/{criado['id']}/status",
        json={"status": "concluido"},
        headers=auth_headers,
    )

    r = api_client.patch(
        f"/api/v1/pedidos/{criado['id']}/status",
        json={"status": "aberto"},
        headers=auth_headers,
    )

    assert r.status_code == 409


def test_patch_status_pedido_inexistente_retorna_404(
    api_client: TestClient, auth_headers: dict
) -> None:
    """PATCH em pedido inexistente retorna 404 ProblemDetail."""
    r = api_client.patch(
        "/api/v1/pedidos/9999/status",
        json={"status": "em_andamento"},
        headers=auth_headers,
    )

    assert r.status_code == 404
    body = r.json()
    assert body["title"] == "Pedido não encontrado"


def test_patch_status_payload_invalido_retorna_422(
    api_client: TestClient, auth_headers: dict
) -> None:
    """PATCH com status fora do enum retorna 422 ProblemDetail."""
    criado = api_client.post("/api/v1/pedidos", json=_VALID_PAYLOAD, headers=auth_headers).json()

    r = api_client.patch(
        f"/api/v1/pedidos/{criado['id']}/status",
        json={"status": "arquivado"},
        headers=auth_headers,
    )

    assert r.status_code == 422
    assert r.json()["title"] == "Erro de validação"


# --- Edição (PATCH) e exclusão (DELETE) de pedido com autorização autor/admin ---


def test_patch_pedido_pelo_autor_atualiza_campos(
    api_client: TestClient, auth_headers: dict
) -> None:
    """PATCH /api/v1/pedidos/{id} pelo autor atualiza campos e retorna 200."""
    criado = api_client.post("/api/v1/pedidos", json=_VALID_PAYLOAD, headers=auth_headers).json()

    r = api_client.patch(
        f"/api/v1/pedidos/{criado['id']}",
        json={"titulo": "Título atualizado"},
        headers=auth_headers,
    )

    assert r.status_code == 200
    assert r.json()["titulo"] == "Título atualizado"


def test_patch_pedido_sem_auth_retorna_401(api_client: TestClient, auth_headers: dict) -> None:
    """PATCH /api/v1/pedidos/{id} sem Bearer retorna 401."""
    criado = api_client.post("/api/v1/pedidos", json=_VALID_PAYLOAD, headers=auth_headers).json()

    r = api_client.patch(f"/api/v1/pedidos/{criado['id']}", json={"titulo": "Novo título"})

    assert r.status_code == 401


def test_patch_pedido_por_nao_autor_retorna_403(
    api_client: TestClient, auth_headers: dict, auth_headers_outro: dict
) -> None:
    """PATCH /api/v1/pedidos/{id} por quem não é autor nem admin retorna 403."""
    criado = api_client.post("/api/v1/pedidos", json=_VALID_PAYLOAD, headers=auth_headers).json()

    r = api_client.patch(
        f"/api/v1/pedidos/{criado['id']}",
        json={"titulo": "Tentativa indevida"},
        headers=auth_headers_outro,
    )

    assert r.status_code == 403
    assert r.json()["title"] == "Acesso negado"


def test_patch_pedido_por_admin_permitido(
    api_client: TestClient, auth_headers: dict, admin_headers: dict
) -> None:
    """Admin pode editar pedido de outro autor."""
    criado = api_client.post("/api/v1/pedidos", json=_VALID_PAYLOAD, headers=auth_headers).json()

    r = api_client.patch(
        f"/api/v1/pedidos/{criado['id']}",
        json={"titulo": "Editado pelo admin"},
        headers=admin_headers,
    )

    assert r.status_code == 200
    assert r.json()["titulo"] == "Editado pelo admin"


def test_patch_pedido_inexistente_retorna_404(api_client: TestClient, auth_headers: dict) -> None:
    """PATCH em pedido inexistente retorna 404 ProblemDetail."""
    r = api_client.patch("/api/v1/pedidos/9999", json={"titulo": "Qualquer"}, headers=auth_headers)

    assert r.status_code == 404
    assert r.json()["title"] == "Pedido não encontrado"


def test_delete_pedido_pelo_autor_retorna_204_e_soft_delete(
    api_client: TestClient, auth_headers: dict
) -> None:
    """DELETE pelo autor faz soft-delete (204) e o pedido some das leituras."""
    criado = api_client.post("/api/v1/pedidos", json=_VALID_PAYLOAD, headers=auth_headers).json()

    r = api_client.delete(f"/api/v1/pedidos/{criado['id']}", headers=auth_headers)

    assert r.status_code == 204
    assert api_client.get(f"/api/v1/pedidos/{criado['id']}").status_code == 404


def test_delete_pedido_sem_auth_retorna_401(api_client: TestClient, auth_headers: dict) -> None:
    """DELETE sem Bearer retorna 401."""
    criado = api_client.post("/api/v1/pedidos", json=_VALID_PAYLOAD, headers=auth_headers).json()

    r = api_client.delete(f"/api/v1/pedidos/{criado['id']}")

    assert r.status_code == 401


def test_delete_pedido_por_nao_autor_retorna_403(
    api_client: TestClient, auth_headers: dict, auth_headers_outro: dict
) -> None:
    """DELETE por quem não é autor nem admin retorna 403."""
    criado = api_client.post("/api/v1/pedidos", json=_VALID_PAYLOAD, headers=auth_headers).json()

    r = api_client.delete(f"/api/v1/pedidos/{criado['id']}", headers=auth_headers_outro)

    assert r.status_code == 403
    assert r.json()["title"] == "Acesso negado"


def test_delete_pedido_por_admin_permitido(
    api_client: TestClient, auth_headers: dict, admin_headers: dict
) -> None:
    """Admin pode remover pedido de outro autor (204)."""
    criado = api_client.post("/api/v1/pedidos", json=_VALID_PAYLOAD, headers=auth_headers).json()

    r = api_client.delete(f"/api/v1/pedidos/{criado['id']}", headers=admin_headers)

    assert r.status_code == 204


def test_delete_pedido_inexistente_retorna_404(api_client: TestClient, auth_headers: dict) -> None:
    """DELETE em pedido inexistente retorna 404 ProblemDetail."""
    r = api_client.delete("/api/v1/pedidos/9999", headers=auth_headers)

    assert r.status_code == 404
    assert r.json()["title"] == "Pedido não encontrado"


def test_get_pedidos_tolera_localizacao_legada_vazia(api_client: TestClient, db_session) -> None:
    """Pedido legado com cidade/estado vazios é lido sem 500.

    A migração de produção fez backfill de `cidade=''`/`estado=''` em pedidos
    pré-existentes; a leitura (`PedidoRead`) deve tolerar esses valores em vez de
    falhar a validação e estourar 500 na listagem/detalhe.
    """
    from app.models.enums import CategoriaEnum, StatusPedidoEnum, UrgenciaEnum
    from app.models.pedido import PedidoAjuda

    legado = PedidoAjuda(
        titulo="Pedido legado sem localização",
        descricao="Criado antes dos campos de localização entrarem no schema.",
        categoria=CategoriaEnum.RESGATE,
        urgencia=UrgenciaEnum.MEDIA,
        status=StatusPedidoEnum.ABERTO,
        contato="11999990000",
        cidade="",
        estado="",
    )
    db_session.add(legado)
    db_session.commit()
    db_session.refresh(legado)

    r_lista = api_client.get("/api/v1/pedidos")
    assert r_lista.status_code == 200
    assert legado.id in [p["id"] for p in r_lista.json()["items"]]

    r_detalhe = api_client.get(f"/api/v1/pedidos/{legado.id}")
    assert r_detalhe.status_code == 200
    assert r_detalhe.json()["estado"] == ""
    assert r_detalhe.json()["cidade"] == ""
