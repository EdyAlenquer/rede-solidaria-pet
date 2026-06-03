"""Testes da Fase A1 — hardening do modelo de dados.

Cobre soft-delete, constraints de banco do doador, enforcement de FK no
engine de aplicação e awareness de timezone nos timestamps.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import CategoriaEnum
from app.models.doador import DoadorVoluntario
from app.models.enums import StatusPedidoEnum, UrgenciaEnum
from app.repositories.pedido_repository import PedidoRepository
from app.schemas import PedidoCreate, PedidoStatusUpdate
from app.schemas.pedido import PedidoRead


def _pedido(**overrides) -> PedidoCreate:
    """Constrói um `PedidoCreate` válido para os testes de hardening."""
    base = {
        "titulo": "Cãozinho ferido",
        "descricao": "Encontrado na rua X, precisa de atendimento.",
        "categoria": CategoriaEnum.RESGATE,
        "urgencia": UrgenciaEnum.ALTA,
        "contato": "11999990000",
        "cidade": "São Paulo",
        "estado": "SP",
        "consentimento_aceito": True,
    }
    base.update(overrides)
    return PedidoCreate(**base)


def test_soft_delete_oculta_pedido_de_get_e_list(db_session: Session) -> None:
    """Após `soft_delete`, o pedido some de `get_by_id`, `list` e `count`."""
    repo = PedidoRepository(db_session)
    pedido = repo.create(_pedido())

    removido = repo.soft_delete(pedido.id)

    assert removido is True
    assert repo.get_by_id(pedido.id) is None
    assert repo.list() == []
    assert repo.count() == 0


def test_soft_delete_nao_exclui_fisicamente(db_session: Session) -> None:
    """`soft_delete` apenas preenche `deleted_at`; a linha permanece no banco."""
    repo = PedidoRepository(db_session)
    pedido = repo.create(_pedido())

    repo.soft_delete(pedido.id)

    total = db_session.scalar(text("SELECT COUNT(*) FROM pedidos"))
    assert total == 1
    deleted_at = db_session.scalar(
        text("SELECT deleted_at FROM pedidos WHERE id = :id"), {"id": pedido.id}
    )
    assert deleted_at is not None


def test_soft_delete_retorna_false_para_inexistente(db_session: Session) -> None:
    """`soft_delete` em id inexistente retorna False."""
    repo = PedidoRepository(db_session)
    assert repo.soft_delete(9999) is False


def test_soft_delete_e_idempotente(db_session: Session) -> None:
    """Soft-deletar duas vezes não reativa nem dá erro; segunda chamada retorna False."""
    repo = PedidoRepository(db_session)
    pedido = repo.create(_pedido())

    assert repo.soft_delete(pedido.id) is True
    assert repo.soft_delete(pedido.id) is False


def test_list_paginated_exclui_soft_deleted(db_session: Session) -> None:
    """`list_paginated` não conta nem retorna pedidos soft-deletados."""
    repo = PedidoRepository(db_session)
    vivo = repo.create(_pedido(titulo="Pedido vivo"))
    morto = repo.create(_pedido(titulo="Pedido morto"))
    repo.soft_delete(morto.id)

    resultado = repo.list_paginated(page=1, page_size=10)

    assert resultado.total == 1
    assert [p.id for p in resultado.items] == [vivo.id]


def test_update_status_ignora_pedido_soft_deletado(db_session: Session) -> None:
    """`update_status` não atinge pedidos soft-deletados (tratados como inexistentes)."""
    repo = PedidoRepository(db_session)
    pedido = repo.create(_pedido())
    repo.soft_delete(pedido.id)

    resultado = repo.update_status(
        pedido.id, PedidoStatusUpdate(status=StatusPedidoEnum.EM_ANDAMENTO)
    )
    assert resultado is None


def test_doador_check_constraint_rejeita_sem_contato(db_session: Session) -> None:
    """O banco rejeita doador sem telefone e sem email (CheckConstraint)."""
    db_session.add(DoadorVoluntario(nome="Sem Contato"))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_doador_unique_constraint_rejeita_email_duplicado(db_session: Session) -> None:
    """O banco rejeita dois doadores com o mesmo email (UniqueConstraint)."""
    db_session.add(DoadorVoluntario(nome="Maria", email="dup@example.com"))
    db_session.flush()
    db_session.add(DoadorVoluntario(nome="João", email="dup@example.com"))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_app_engine_ativa_pragma_foreign_keys() -> None:
    """O engine de `app.database` ativa `PRAGMA foreign_keys=ON` em SQLite."""
    from app.database import engine

    with engine.connect() as conn:
        valor = conn.exec_driver_sql("PRAGMA foreign_keys").scalar()
    assert valor == 1


def test_pedido_read_data_criacao_tem_tzinfo(db_session: Session) -> None:
    """`PedidoRead.data_criacao` é timezone-aware (offset não-nulo)."""
    repo = PedidoRepository(db_session)
    pedido = repo.create(_pedido())

    lido = PedidoRead.model_validate(pedido)

    assert lido.data_criacao.tzinfo is not None
    assert lido.data_criacao.utcoffset() is not None
