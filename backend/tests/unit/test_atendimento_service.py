"""Testes do AtendimentoService (regras de negócio sobre AtendimentoRepository)."""

import pytest
from sqlalchemy.orm import Session

from app.core.errors import DoadorNotFoundError, PedidoNotAtendivelError, PedidoNotFoundError
from app.models.enums import StatusPedidoEnum, UrgenciaEnum
from app.repositories.atendimento_repository import AtendimentoRepository
from app.repositories.doador_repository import DoadorRepository
from app.repositories.pedido_repository import PedidoRepository
from app.schemas import AtendimentoCreate, DoadorCreate, PedidoCreate, PedidoStatusUpdate
from app.services import AtendimentoService


def _pedido_payload(**overrides) -> PedidoCreate:
    """Constrói um `PedidoCreate` válido para os testes."""
    base = {
        "titulo": "Pedido teste",
        "descricao": "Descrição longa o suficiente para passar.",
        "categoria": "resgate",
        "urgencia": UrgenciaEnum.ALTA,
        "contato": "11999990000",
    }
    base.update(overrides)
    return PedidoCreate(**base)


def _service(db_session: Session) -> AtendimentoService:
    """Constrói o serviço com repositórios reais para a sessão de teste."""
    return AtendimentoService(
        atendimento_repository=AtendimentoRepository(db_session),
        pedido_repository=PedidoRepository(db_session),
        doador_repository=DoadorRepository(db_session),
    )


def test_atendimento_service_eh_exportado_pelo_pacote_de_servicos() -> None:
    """`AtendimentoService` está disponível pelo pacote público de serviços."""
    assert AtendimentoService.__name__ == "AtendimentoService"


def test_create_move_pedido_aberto_para_em_andamento(db_session: Session) -> None:
    """Criar atendimento para pedido aberto muda o status para em_andamento."""
    pedido_repo = PedidoRepository(db_session)
    doador_repo = DoadorRepository(db_session)
    pedido = pedido_repo.create(_pedido_payload())
    doador = doador_repo.create(DoadorCreate(nome="Maria", telefone="11988887777"))

    atendimento = _service(db_session).create(
        pedido.id,
        AtendimentoCreate(doador_id=doador.id, tipo_ajuda="ração"),
    )

    assert atendimento.id is not None
    assert pedido_repo.get_by_id(pedido.id).status is StatusPedidoEnum.EM_ANDAMENTO


def test_create_mantem_pedido_em_andamento(db_session: Session) -> None:
    """Criar atendimento para pedido em_andamento mantém o status atual."""
    pedido_repo = PedidoRepository(db_session)
    doador_repo = DoadorRepository(db_session)
    pedido = pedido_repo.create(_pedido_payload())
    pedido_repo.update_status(pedido.id, PedidoStatusUpdate(status=StatusPedidoEnum.EM_ANDAMENTO))
    doador = doador_repo.create(DoadorCreate(nome="Maria", telefone="11988887777"))

    _service(db_session).create(
        pedido.id,
        AtendimentoCreate(doador_id=doador.id, tipo_ajuda="ração"),
    )

    assert pedido_repo.get_by_id(pedido.id).status is StatusPedidoEnum.EM_ANDAMENTO


def test_create_lanca_pedido_not_found_para_pedido_inexistente(db_session: Session) -> None:
    """Criar atendimento para pedido inexistente levanta `PedidoNotFoundError`."""
    doador = DoadorRepository(db_session).create(DoadorCreate(nome="Maria", telefone="11988887777"))

    with pytest.raises(PedidoNotFoundError):
        _service(db_session).create(
            9999,
            AtendimentoCreate(doador_id=doador.id, tipo_ajuda="ração"),
        )


def test_create_lanca_doador_not_found_para_doador_inexistente(db_session: Session) -> None:
    """Criar atendimento com doador inexistente levanta `DoadorNotFoundError`."""
    pedido = PedidoRepository(db_session).create(_pedido_payload())

    with pytest.raises(DoadorNotFoundError):
        _service(db_session).create(
            pedido.id,
            AtendimentoCreate(doador_id=9999, tipo_ajuda="ração"),
        )


def test_create_lanca_pedido_not_atendivel_para_pedido_concluido(db_session: Session) -> None:
    """Criar atendimento para pedido concluido levanta `PedidoNotAtendivelError`."""
    pedido_repo = PedidoRepository(db_session)
    doador_repo = DoadorRepository(db_session)
    pedido = pedido_repo.create(_pedido_payload())
    pedido_repo.update_status(pedido.id, PedidoStatusUpdate(status=StatusPedidoEnum.CONCLUIDO))
    doador = doador_repo.create(DoadorCreate(nome="Maria", telefone="11988887777"))

    with pytest.raises(PedidoNotAtendivelError):
        _service(db_session).create(
            pedido.id,
            AtendimentoCreate(doador_id=doador.id, tipo_ajuda="ração"),
        )


def test_create_desfaz_atendimento_se_atualizacao_de_status_falhar(
    db_session: Session, monkeypatch
) -> None:
    """Falha ao atualizar status não deixa atendimento parcial persistido."""
    pedido_repo = PedidoRepository(db_session)
    doador_repo = DoadorRepository(db_session)
    atendimento_repo = AtendimentoRepository(db_session)
    pedido = pedido_repo.create(_pedido_payload())
    doador = doador_repo.create(DoadorCreate(nome="Maria", telefone="11988887777"))

    def _falha_update_status(*args, **kwargs) -> None:
        raise RuntimeError("falha simulada na atualização")

    monkeypatch.setattr(pedido_repo, "update_status", _falha_update_status)

    with pytest.raises(RuntimeError, match="falha simulada"):
        AtendimentoService(
            atendimento_repository=atendimento_repo,
            pedido_repository=pedido_repo,
            doador_repository=doador_repo,
        ).create(
            pedido.id,
            AtendimentoCreate(doador_id=doador.id, tipo_ajuda="ração"),
        )

    db_session.rollback()
    assert atendimento_repo.list_by_pedido(pedido.id) == []


def test_list_by_pedido_lanca_pedido_not_found_para_pedido_inexistente(
    db_session: Session,
) -> None:
    """Listar atendimentos de pedido inexistente levanta `PedidoNotFoundError`."""
    with pytest.raises(PedidoNotFoundError):
        _service(db_session).list_by_pedido(9999)
