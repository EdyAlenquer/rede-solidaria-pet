"""Testes do AtendimentoRepository."""

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.enums import UrgenciaEnum
from app.repositories.atendimento_repository import AtendimentoRepository
from app.repositories.doador_repository import DoadorRepository
from app.repositories.pedido_repository import PedidoRepository
from app.schemas import AtendimentoCreate, DoadorCreate, PedidoCreate


@pytest.fixture
def pedido_existente(db_session: Session):
    """Cria um pedido para vincular atendimentos."""
    repo = PedidoRepository(db_session)
    return repo.create(
        PedidoCreate(
            titulo="Pedido teste",
            descricao="Descrição longa o suficiente para passar.",
            categoria="resgate",
            urgencia=UrgenciaEnum.ALTA,
            contato="11999990000",
            cidade="São Paulo",
            estado="SP",
            consentimento_aceito=True,
        )
    )


@pytest.fixture
def doador_existente(db_session: Session):
    """Cria um doador para registrar atendimentos."""
    repo = DoadorRepository(db_session)
    return repo.create(
        DoadorCreate(nome="Maria", telefone="11988887777", consentimento_aceito=True)
    )


def test_create_persiste_atendimento_e_relaciona_entidades(
    db_session: Session, pedido_existente, doador_existente
) -> None:
    """`create` persiste o atendimento com FKs corretas."""
    repo = AtendimentoRepository(db_session)

    atendimento = repo.create(
        pedido_existente.id,
        AtendimentoCreate(tipo_ajuda="ração"),
        doador_id=doador_existente.id,
    )

    assert atendimento.id is not None
    assert atendimento.pedido_id == pedido_existente.id
    assert atendimento.doador_id == doador_existente.id
    assert atendimento.tipo_ajuda == "ração"
    assert atendimento.data_contato is not None


def test_create_falha_quando_pedido_nao_existe(db_session: Session, doador_existente) -> None:
    """FK inválido de pedido faz o flush falhar (com FK pragma ativo)."""
    repo = AtendimentoRepository(db_session)

    with pytest.raises(IntegrityError):
        repo.create(
            9999,
            AtendimentoCreate(tipo_ajuda="ração"),
            doador_id=doador_existente.id,
        )


def test_create_falha_quando_doador_nao_existe(db_session: Session, pedido_existente) -> None:
    """FK inválido de doador faz o flush falhar (com FK pragma ativo)."""
    repo = AtendimentoRepository(db_session)

    with pytest.raises(IntegrityError):
        repo.create(
            pedido_existente.id,
            AtendimentoCreate(tipo_ajuda="ração"),
            doador_id=9999,
        )


def test_create_segundo_atendimento_mesmo_doador_e_pedido_viola_unique(
    db_session: Session, pedido_existente, doador_existente
) -> None:
    """UniqueConstraint(pedido_id, doador_id) impede atendimento duplicado."""
    repo = AtendimentoRepository(db_session)
    repo.create(
        pedido_existente.id,
        AtendimentoCreate(tipo_ajuda="ração"),
        doador_id=doador_existente.id,
    )

    with pytest.raises(IntegrityError):
        repo.create(
            pedido_existente.id,
            AtendimentoCreate(tipo_ajuda="transporte"),
            doador_id=doador_existente.id,
        )


def test_list_by_pedido_retorna_apenas_atendimentos_do_pedido(
    db_session: Session, pedido_existente, doador_existente
) -> None:
    """`list_by_pedido` filtra pelos pedidos relacionados."""
    repo = AtendimentoRepository(db_session)
    outro_doador = DoadorRepository(db_session).create(
        DoadorCreate(nome="João", telefone="11977776666", consentimento_aceito=True)
    )
    repo.create(
        pedido_existente.id,
        AtendimentoCreate(tipo_ajuda="ração"),
        doador_id=doador_existente.id,
    )
    repo.create(
        pedido_existente.id,
        AtendimentoCreate(tipo_ajuda="transporte"),
        doador_id=outro_doador.id,
    )

    atendimentos = repo.list_by_pedido(pedido_existente.id)

    assert len(atendimentos) == 2
    assert {a.tipo_ajuda for a in atendimentos} == {"ração", "transporte"}


def test_list_by_pedido_retorna_lista_vazia_quando_nao_ha_atendimentos(
    db_session: Session, pedido_existente
) -> None:
    """`list_by_pedido` retorna lista vazia quando não há atendimentos."""
    repo = AtendimentoRepository(db_session)
    assert repo.list_by_pedido(pedido_existente.id) == []
