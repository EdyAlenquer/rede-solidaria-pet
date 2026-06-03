"""Testes do PedidoRepository contra SQLite em memória."""

from sqlalchemy.orm import Session

from app.models.enums import EspecieEnum, PorteEnum, StatusPedidoEnum, UrgenciaEnum
from app.repositories.pedido_repository import PedidoRepository
from app.schemas import PedidoCreate, PedidoStatusUpdate, PedidoUpdate


def _build_payload(**overrides) -> PedidoCreate:
    """Constrói um PedidoCreate válido com overrides opcionais."""
    base = {
        "titulo": "Cãozinho ferido",
        "descricao": "Encontrado na rua X, precisa de atendimento.",
        "categoria": "resgate",
        "urgencia": UrgenciaEnum.ALTA,
        "contato": "11999990000",
        "cidade": "São Paulo",
        "estado": "SP",
        "consentimento_aceito": True,
    }
    base.update(overrides)
    return PedidoCreate(**base)


def test_create_persiste_pedido_com_status_aberto(db_session: Session) -> None:
    """Ao criar, o pedido recebe id e status `ABERTO` por padrão."""
    repo = PedidoRepository(db_session)
    pedido = repo.create(_build_payload())

    assert pedido.id is not None
    assert pedido.status is StatusPedidoEnum.ABERTO
    assert pedido.data_criacao is not None


def test_get_by_id_retorna_pedido_existente(db_session: Session) -> None:
    """`get_by_id` retorna o pedido quando o id existe."""
    repo = PedidoRepository(db_session)
    criado = repo.create(_build_payload())

    encontrado = repo.get_by_id(criado.id)

    assert encontrado is not None
    assert encontrado.id == criado.id


def test_get_by_id_retorna_none_para_id_inexistente(db_session: Session) -> None:
    """`get_by_id` retorna None quando o id não existe."""
    repo = PedidoRepository(db_session)
    assert repo.get_by_id(9999) is None


def test_list_retorna_todos_em_ordem_decrescente_por_data(db_session: Session) -> None:
    """`list` retorna pedidos do mais recente para o mais antigo."""
    repo = PedidoRepository(db_session)
    primeiro = repo.create(_build_payload(titulo="Primeiro pedido"))
    segundo = repo.create(_build_payload(titulo="Segundo pedido"))

    todos = repo.list()

    assert [p.id for p in todos] == [segundo.id, primeiro.id]


def test_list_filtra_por_status(db_session: Session) -> None:
    """`list(status=...)` retorna apenas pedidos com o status informado."""
    repo = PedidoRepository(db_session)
    aberto = repo.create(_build_payload(titulo="Aberto"))
    em_and = repo.create(_build_payload(titulo="Em andamento"))
    repo.update_status(em_and.id, PedidoStatusUpdate(status=StatusPedidoEnum.EM_ANDAMENTO))

    abertos = repo.list(status=StatusPedidoEnum.ABERTO)

    assert [p.id for p in abertos] == [aberto.id]


def test_list_filtra_por_urgencia(db_session: Session) -> None:
    """`list(urgencia=...)` filtra por urgência."""
    repo = PedidoRepository(db_session)
    alta = repo.create(_build_payload(titulo="Alta", urgencia=UrgenciaEnum.ALTA))
    repo.create(_build_payload(titulo="Baixa", urgencia=UrgenciaEnum.BAIXA))

    altas = repo.list(urgencia=UrgenciaEnum.ALTA)

    assert [p.id for p in altas] == [alta.id]


def test_list_filtra_por_categoria(db_session: Session) -> None:
    """`list(categoria=...)` filtra por categoria (igualdade exata)."""
    repo = PedidoRepository(db_session)
    resgate = repo.create(_build_payload(titulo="Resgate", categoria="resgate"))
    repo.create(_build_payload(titulo="Transporte", categoria="transporte"))

    apenas_resgate = repo.list(categoria="resgate")

    assert [p.id for p in apenas_resgate] == [resgate.id]


def test_update_aplica_apenas_campos_informados(db_session: Session) -> None:
    """`update` modifica apenas os campos presentes no payload."""
    repo = PedidoRepository(db_session)
    pedido = repo.create(_build_payload())

    atualizado = repo.update(pedido.id, PedidoUpdate(titulo="Novo título"))

    assert atualizado is not None
    assert atualizado.titulo == "Novo título"
    assert atualizado.categoria == "resgate"  # inalterado


def test_update_status_muda_status(db_session: Session) -> None:
    """`update_status` aplica o novo status corretamente."""
    repo = PedidoRepository(db_session)
    pedido = repo.create(_build_payload())

    atualizado = repo.update_status(
        pedido.id, PedidoStatusUpdate(status=StatusPedidoEnum.CONCLUIDO)
    )

    assert atualizado is not None
    assert atualizado.status is StatusPedidoEnum.CONCLUIDO


def test_update_status_retorna_none_para_id_inexistente(db_session: Session) -> None:
    """`update_status` retorna None se o pedido não existir."""
    repo = PedidoRepository(db_session)
    assert (
        repo.update_status(9999, PedidoStatusUpdate(status=StatusPedidoEnum.EM_ANDAMENTO)) is None
    )


def test_list_aceita_filtro_q_busca_textual(db_session: Session) -> None:
    """`list(q=...)` filtra por substring case-insensitive em titulo/descricao."""
    repo = PedidoRepository(db_session)
    repo.create(_build_payload(titulo="Cãozinho ferido", descricao="encontrado na rua"))
    repo.create(_build_payload(titulo="Gata grávida", descricao="precisa de abrigo"))
    repo.create(_build_payload(titulo="Doação de ração", descricao="estoque baixo"))

    resultado_titulo = repo.list(q="cãozinho")
    resultado_desc = repo.list(q="abrigo")
    resultado_vazio = repo.list(q="cavalo")

    assert {p.titulo for p in resultado_titulo} == {"Cãozinho ferido"}
    assert {p.titulo for p in resultado_desc} == {"Gata grávida"}
    assert resultado_vazio == []


def test_list_paginated_retorna_pagina_correta(db_session: Session) -> None:
    """`list_paginated` aplica LIMIT/OFFSET e retorna items + total."""
    repo = PedidoRepository(db_session)
    criados = [repo.create(_build_payload(titulo=f"Pedido {i}")) for i in range(5)]
    # Ordem decrescente por data_criacao (com id desc como secundário)
    esperado_ordem = list(reversed(criados))

    pagina1 = repo.list_paginated(page=1, page_size=2)
    pagina2 = repo.list_paginated(page=2, page_size=2)
    pagina3 = repo.list_paginated(page=3, page_size=2)

    assert pagina1.total == 5
    assert [p.id for p in pagina1.items] == [esperado_ordem[0].id, esperado_ordem[1].id]
    assert [p.id for p in pagina2.items] == [esperado_ordem[2].id, esperado_ordem[3].id]
    assert [p.id for p in pagina3.items] == [esperado_ordem[4].id]


def test_list_paginated_aplica_filtros(db_session: Session) -> None:
    """`list_paginated` respeita filtros (status, urgencia, categoria, q)."""
    repo = PedidoRepository(db_session)
    repo.create(_build_payload(titulo="Alta urgência", urgencia=UrgenciaEnum.ALTA))
    repo.create(_build_payload(titulo="Baixa urgência", urgencia=UrgenciaEnum.BAIXA))

    resultado = repo.list_paginated(page=1, page_size=10, urgencia=UrgenciaEnum.ALTA)

    assert resultado.total == 1
    assert {p.titulo for p in resultado.items} == {"Alta urgência"}


def test_count_respeita_filtros(db_session: Session) -> None:
    """`count` retorna total absoluto ou filtrado."""
    repo = PedidoRepository(db_session)
    repo.create(_build_payload(urgencia=UrgenciaEnum.ALTA))
    repo.create(_build_payload(urgencia=UrgenciaEnum.ALTA))
    repo.create(_build_payload(urgencia=UrgenciaEnum.BAIXA))

    assert repo.count() == 3
    assert repo.count(urgencia=UrgenciaEnum.ALTA) == 2
    assert repo.count(urgencia=UrgenciaEnum.MEDIA) == 0


def test_list_filtra_por_cidade_e_estado(db_session: Session) -> None:
    """`list(cidade=..., estado=...)` filtra por igualdade exata."""
    repo = PedidoRepository(db_session)
    sp = repo.create(_build_payload(titulo="Pedido SP", cidade="São Paulo", estado="SP"))
    repo.create(_build_payload(titulo="Pedido RJ", cidade="Rio de Janeiro", estado="RJ"))

    apenas_sp = repo.list(cidade="São Paulo", estado="SP")

    assert [p.id for p in apenas_sp] == [sp.id]


def test_list_filtra_por_especie_e_porte(db_session: Session) -> None:
    """`list(especie=..., porte=...)` filtra por igualdade exata."""
    repo = PedidoRepository(db_session)
    alvo = repo.create(
        _build_payload(titulo="Cão médio", especie=EspecieEnum.CAO, porte=PorteEnum.MEDIO)
    )
    repo.create(_build_payload(titulo="Gato", especie=EspecieEnum.GATO, porte=PorteEnum.PEQUENO))

    resultado = repo.list(especie=EspecieEnum.CAO, porte=PorteEnum.MEDIO)

    assert [p.id for p in resultado] == [alvo.id]


def test_list_ordena_por_distancia_quando_ponto_de_referencia(db_session: Session) -> None:
    """Com lat/lon de referência, a listagem ordena do mais próximo ao mais distante."""
    repo = PedidoRepository(db_session)
    # São Paulo ~ (-23.55, -46.63); referência próxima a SP.
    longe = repo.create(_build_payload(titulo="Manaus", latitude=-3.10, longitude=-60.02))
    perto = repo.create(_build_payload(titulo="Campinas", latitude=-22.90, longitude=-47.06))

    ordenado = repo.list(latitude=-23.55, longitude=-46.63)

    assert [p.id for p in ordenado] == [perto.id, longe.id]


def test_list_paginated_aceita_novos_filtros(db_session: Session) -> None:
    """`list_paginated` respeita os filtros de cidade/estado/especie/porte."""
    repo = PedidoRepository(db_session)
    repo.create(_build_payload(titulo="SP cão", cidade="São Paulo", estado="SP"))
    repo.create(_build_payload(titulo="Pedido RJ", cidade="Rio de Janeiro", estado="RJ"))

    resultado = repo.list_paginated(page=1, page_size=10, cidade="São Paulo", estado="SP")

    assert resultado.total == 1
    assert {p.titulo for p in resultado.items} == {"SP cão"}


def test_pedido_persiste_imagens_via_relationship(db_session: Session) -> None:
    """Imagens anexadas via relationship são persistidas e ordenadas por `ordem`."""
    from app.models.imagem import ImagemPedido

    repo = PedidoRepository(db_session)
    pedido = repo.create(_build_payload())
    pedido.imagens.append(ImagemPedido(url="https://cdn/b.jpg", ordem=1))
    pedido.imagens.append(ImagemPedido(url="https://cdn/a.jpg", ordem=0))
    db_session.commit()

    recarregado = repo.get_by_id(pedido.id)
    assert [img.url for img in recarregado.imagens] == ["https://cdn/a.jpg", "https://cdn/b.jpg"]
