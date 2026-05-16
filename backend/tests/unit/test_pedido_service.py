"""Testes do PedidoService (regras de negócio sobre PedidoRepository)."""

import pytest
from sqlalchemy.orm import Session

from app.core.errors import InvalidStatusTransitionError, PedidoNotFoundError
from app.models.enums import StatusPedidoEnum, UrgenciaEnum
from app.repositories.pedido_repository import PedidoRepository
from app.schemas import PedidoCreate, PedidoStatusUpdate
from app.services.pedido_service import PedidoService


def _payload(**overrides) -> PedidoCreate:
    """Constrói um PedidoCreate válido para os testes."""
    base = {
        "titulo": "Resgate",
        "descricao": "Descrição com texto suficiente para passar validação.",
        "categoria": "resgate",
        "urgencia": UrgenciaEnum.ALTA,
        "contato": "11999990000",
    }
    base.update(overrides)
    return PedidoCreate(**base)


def test_create_delega_ao_repositorio(db_session: Session) -> None:
    """`create` salva via repositório e retorna o pedido novo."""
    service = PedidoService(PedidoRepository(db_session))
    pedido = service.create(_payload())
    assert pedido.id is not None
    assert pedido.status is StatusPedidoEnum.ABERTO


def test_get_by_id_retorna_pedido_existente(db_session: Session) -> None:
    """`get_by_id` retorna o pedido quando o id existe."""
    service = PedidoService(PedidoRepository(db_session))
    criado = service.create(_payload())
    encontrado = service.get_by_id(criado.id)
    assert encontrado.id == criado.id


def test_get_by_id_levanta_pedido_not_found(db_session: Session) -> None:
    """`get_by_id` levanta `PedidoNotFoundError` quando o id não existe."""
    service = PedidoService(PedidoRepository(db_session))
    with pytest.raises(PedidoNotFoundError):
        service.get_by_id(9999)


def test_change_status_aberto_para_em_andamento_permitido(db_session: Session) -> None:
    """aberto -> em_andamento é permitido."""
    service = PedidoService(PedidoRepository(db_session))
    pedido = service.create(_payload())
    atualizado = service.change_status(
        pedido.id, PedidoStatusUpdate(status=StatusPedidoEnum.EM_ANDAMENTO)
    )
    assert atualizado.status is StatusPedidoEnum.EM_ANDAMENTO


def test_change_status_aberto_para_concluido_permitido(db_session: Session) -> None:
    """aberto -> concluido é permitido (pulo direto)."""
    service = PedidoService(PedidoRepository(db_session))
    pedido = service.create(_payload())
    atualizado = service.change_status(
        pedido.id, PedidoStatusUpdate(status=StatusPedidoEnum.CONCLUIDO)
    )
    assert atualizado.status is StatusPedidoEnum.CONCLUIDO


def test_change_status_em_andamento_para_aberto_bloqueado(db_session: Session) -> None:
    """em_andamento -> aberto é bloqueado (regressão)."""
    service = PedidoService(PedidoRepository(db_session))
    pedido = service.create(_payload())
    service.change_status(pedido.id, PedidoStatusUpdate(status=StatusPedidoEnum.EM_ANDAMENTO))

    with pytest.raises(InvalidStatusTransitionError):
        service.change_status(pedido.id, PedidoStatusUpdate(status=StatusPedidoEnum.ABERTO))


def test_change_status_concluido_para_qualquer_outro_bloqueado(db_session: Session) -> None:
    """concluido é estado terminal — não pode ir para nenhum outro."""
    service = PedidoService(PedidoRepository(db_session))
    pedido = service.create(_payload())
    service.change_status(pedido.id, PedidoStatusUpdate(status=StatusPedidoEnum.CONCLUIDO))

    with pytest.raises(InvalidStatusTransitionError):
        service.change_status(pedido.id, PedidoStatusUpdate(status=StatusPedidoEnum.EM_ANDAMENTO))
    with pytest.raises(InvalidStatusTransitionError):
        service.change_status(pedido.id, PedidoStatusUpdate(status=StatusPedidoEnum.ABERTO))


def test_change_status_idempotente_e_no_op(db_session: Session) -> None:
    """Mudar para o mesmo status atual é no-op (retorna sem erro)."""
    service = PedidoService(PedidoRepository(db_session))
    pedido = service.create(_payload())
    atualizado = service.change_status(
        pedido.id, PedidoStatusUpdate(status=StatusPedidoEnum.ABERTO)
    )
    assert atualizado.status is StatusPedidoEnum.ABERTO


def test_change_status_pedido_inexistente_levanta_not_found(db_session: Session) -> None:
    """Tentar mudar status de pedido inexistente levanta PedidoNotFoundError."""
    service = PedidoService(PedidoRepository(db_session))
    with pytest.raises(PedidoNotFoundError):
        service.change_status(9999, PedidoStatusUpdate(status=StatusPedidoEnum.EM_ANDAMENTO))
