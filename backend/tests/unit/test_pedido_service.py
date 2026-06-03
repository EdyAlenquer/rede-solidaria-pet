"""Testes do PedidoService (regras de negócio sobre PedidoRepository)."""

import pytest
from sqlalchemy.orm import Session

from app.core.errors import InvalidStatusTransitionError, PedidoNotFoundError
from app.models.enums import PapelUsuarioEnum, StatusPedidoEnum, UrgenciaEnum
from app.models.usuario import Usuario
from app.repositories.pedido_repository import PedidoRepository
from app.schemas import PedidoCreate, PedidoStatusUpdate
from app.services.pedido_service import PedidoService


@pytest.fixture
def admin(db_session: Session) -> Usuario:
    """Cria e persiste um usuário administrador para autorizar as operações.

    Args:
        db_session: sessão de teste.

    Returns:
        Usuário com papel ADMIN (autoriza qualquer mudança de pedido).
    """
    usuario = Usuario(
        nome="Admin",
        email="admin-service@example.com",
        senha_hash="x",
        papel=PapelUsuarioEnum.ADMIN,
    )
    db_session.add(usuario)
    db_session.commit()
    db_session.refresh(usuario)
    return usuario


def _payload(**overrides) -> PedidoCreate:
    """Constrói um PedidoCreate válido para os testes."""
    base = {
        "titulo": "Resgate",
        "descricao": "Descrição com texto suficiente para passar validação.",
        "categoria": "resgate",
        "urgencia": UrgenciaEnum.ALTA,
        "contato": "11999990000",
        "cidade": "São Paulo",
        "estado": "SP",
        "consentimento_aceito": True,
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


def _avancar(
    service: PedidoService, pedido_id: int, usuario: Usuario, *destinos: StatusPedidoEnum
) -> None:
    """Aplica uma sequência de transições válidas para posicionar o pedido.

    Args:
        service: serviço sob teste.
        pedido_id: id do pedido a movimentar.
        usuario: usuário autorizado a mudar o status.
        destinos: status a aplicar em ordem.
    """
    for destino in destinos:
        service.change_status(pedido_id, PedidoStatusUpdate(status=destino), usuario=usuario)


# --- Transições VÁLIDAS (uma por aresta do mapa de adjacência) ---


def test_aberto_para_em_andamento_permitido(db_session: Session, admin: Usuario) -> None:
    """ABERTO -> EM_ANDAMENTO é permitido."""
    service = PedidoService(PedidoRepository(db_session))
    pedido = service.create(_payload())
    atualizado = service.change_status(
        pedido.id, PedidoStatusUpdate(status=StatusPedidoEnum.EM_ANDAMENTO), usuario=admin
    )
    assert atualizado.status is StatusPedidoEnum.EM_ANDAMENTO


def test_aberto_para_cancelado_permitido(db_session: Session, admin: Usuario) -> None:
    """ABERTO -> CANCELADO é permitido."""
    service = PedidoService(PedidoRepository(db_session))
    pedido = service.create(_payload())
    atualizado = service.change_status(
        pedido.id, PedidoStatusUpdate(status=StatusPedidoEnum.CANCELADO), usuario=admin
    )
    assert atualizado.status is StatusPedidoEnum.CANCELADO


def test_em_andamento_para_concluido_permitido(db_session: Session, admin: Usuario) -> None:
    """EM_ANDAMENTO -> CONCLUIDO é permitido."""
    service = PedidoService(PedidoRepository(db_session))
    pedido = service.create(_payload())
    _avancar(service, pedido.id, admin, StatusPedidoEnum.EM_ANDAMENTO)
    atualizado = service.change_status(
        pedido.id, PedidoStatusUpdate(status=StatusPedidoEnum.CONCLUIDO), usuario=admin
    )
    assert atualizado.status is StatusPedidoEnum.CONCLUIDO


def test_em_andamento_para_cancelado_permitido(db_session: Session, admin: Usuario) -> None:
    """EM_ANDAMENTO -> CANCELADO é permitido."""
    service = PedidoService(PedidoRepository(db_session))
    pedido = service.create(_payload())
    _avancar(service, pedido.id, admin, StatusPedidoEnum.EM_ANDAMENTO)
    atualizado = service.change_status(
        pedido.id, PedidoStatusUpdate(status=StatusPedidoEnum.CANCELADO), usuario=admin
    )
    assert atualizado.status is StatusPedidoEnum.CANCELADO


def test_em_andamento_para_aberto_reabrir_permitido(db_session: Session, admin: Usuario) -> None:
    """EM_ANDAMENTO -> ABERTO (reabrir) é permitido."""
    service = PedidoService(PedidoRepository(db_session))
    pedido = service.create(_payload())
    _avancar(service, pedido.id, admin, StatusPedidoEnum.EM_ANDAMENTO)
    atualizado = service.change_status(
        pedido.id, PedidoStatusUpdate(status=StatusPedidoEnum.ABERTO), usuario=admin
    )
    assert atualizado.status is StatusPedidoEnum.ABERTO


def test_concluido_para_em_andamento_reabrir_permitido(db_session: Session, admin: Usuario) -> None:
    """CONCLUIDO -> EM_ANDAMENTO (reabrir) é permitido."""
    service = PedidoService(PedidoRepository(db_session))
    pedido = service.create(_payload())
    _avancar(service, pedido.id, admin, StatusPedidoEnum.EM_ANDAMENTO, StatusPedidoEnum.CONCLUIDO)
    atualizado = service.change_status(
        pedido.id, PedidoStatusUpdate(status=StatusPedidoEnum.EM_ANDAMENTO), usuario=admin
    )
    assert atualizado.status is StatusPedidoEnum.EM_ANDAMENTO


def test_cancelado_para_aberto_reabrir_permitido(db_session: Session, admin: Usuario) -> None:
    """CANCELADO -> ABERTO (reabrir) é permitido."""
    service = PedidoService(PedidoRepository(db_session))
    pedido = service.create(_payload())
    _avancar(service, pedido.id, admin, StatusPedidoEnum.CANCELADO)
    atualizado = service.change_status(
        pedido.id, PedidoStatusUpdate(status=StatusPedidoEnum.ABERTO), usuario=admin
    )
    assert atualizado.status is StatusPedidoEnum.ABERTO


# --- Transições INVÁLIDAS ---


def test_aberto_para_concluido_bloqueado(db_session: Session, admin: Usuario) -> None:
    """ABERTO -> CONCLUIDO (pulo direto) é bloqueado."""
    service = PedidoService(PedidoRepository(db_session))
    pedido = service.create(_payload())
    with pytest.raises(InvalidStatusTransitionError):
        service.change_status(
            pedido.id, PedidoStatusUpdate(status=StatusPedidoEnum.CONCLUIDO), usuario=admin
        )


def test_em_andamento_para_concluido_e_volta_so_via_em_andamento(
    db_session: Session, admin: Usuario
) -> None:
    """CONCLUIDO -> ABERTO é bloqueado (só reabre para EM_ANDAMENTO)."""
    service = PedidoService(PedidoRepository(db_session))
    pedido = service.create(_payload())
    _avancar(service, pedido.id, admin, StatusPedidoEnum.EM_ANDAMENTO, StatusPedidoEnum.CONCLUIDO)
    with pytest.raises(InvalidStatusTransitionError):
        service.change_status(
            pedido.id, PedidoStatusUpdate(status=StatusPedidoEnum.ABERTO), usuario=admin
        )


def test_concluido_para_cancelado_bloqueado(db_session: Session, admin: Usuario) -> None:
    """CONCLUIDO -> CANCELADO é bloqueado."""
    service = PedidoService(PedidoRepository(db_session))
    pedido = service.create(_payload())
    _avancar(service, pedido.id, admin, StatusPedidoEnum.EM_ANDAMENTO, StatusPedidoEnum.CONCLUIDO)
    with pytest.raises(InvalidStatusTransitionError):
        service.change_status(
            pedido.id, PedidoStatusUpdate(status=StatusPedidoEnum.CANCELADO), usuario=admin
        )


def test_cancelado_para_em_andamento_bloqueado(db_session: Session, admin: Usuario) -> None:
    """CANCELADO -> EM_ANDAMENTO é bloqueado (só reabre para ABERTO)."""
    service = PedidoService(PedidoRepository(db_session))
    pedido = service.create(_payload())
    _avancar(service, pedido.id, admin, StatusPedidoEnum.CANCELADO)
    with pytest.raises(InvalidStatusTransitionError):
        service.change_status(
            pedido.id, PedidoStatusUpdate(status=StatusPedidoEnum.EM_ANDAMENTO), usuario=admin
        )


def test_cancelado_para_concluido_bloqueado(db_session: Session, admin: Usuario) -> None:
    """CANCELADO -> CONCLUIDO é bloqueado."""
    service = PedidoService(PedidoRepository(db_session))
    pedido = service.create(_payload())
    _avancar(service, pedido.id, admin, StatusPedidoEnum.CANCELADO)
    with pytest.raises(InvalidStatusTransitionError):
        service.change_status(
            pedido.id, PedidoStatusUpdate(status=StatusPedidoEnum.CONCLUIDO), usuario=admin
        )


def test_change_status_idempotente_e_no_op(db_session: Session, admin: Usuario) -> None:
    """Mudar para o mesmo status atual é no-op (retorna sem erro)."""
    service = PedidoService(PedidoRepository(db_session))
    pedido = service.create(_payload())
    atualizado = service.change_status(
        pedido.id, PedidoStatusUpdate(status=StatusPedidoEnum.ABERTO), usuario=admin
    )
    assert atualizado.status is StatusPedidoEnum.ABERTO


def test_change_status_idempotente_em_cancelado(db_session: Session, admin: Usuario) -> None:
    """CANCELADO -> CANCELADO é no-op idempotente (não levanta erro)."""
    service = PedidoService(PedidoRepository(db_session))
    pedido = service.create(_payload())
    _avancar(service, pedido.id, admin, StatusPedidoEnum.CANCELADO)
    atualizado = service.change_status(
        pedido.id, PedidoStatusUpdate(status=StatusPedidoEnum.CANCELADO), usuario=admin
    )
    assert atualizado.status is StatusPedidoEnum.CANCELADO


def test_change_status_pedido_inexistente_levanta_not_found(
    db_session: Session, admin: Usuario
) -> None:
    """Tentar mudar status de pedido inexistente levanta PedidoNotFoundError."""
    service = PedidoService(PedidoRepository(db_session))
    with pytest.raises(PedidoNotFoundError):
        service.change_status(
            9999, PedidoStatusUpdate(status=StatusPedidoEnum.EM_ANDAMENTO), usuario=admin
        )
