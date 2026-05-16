"""Testes do PedidoRepository contra SQLite em memória."""

from sqlalchemy.orm import Session

from app.models.enums import StatusPedidoEnum, UrgenciaEnum
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
