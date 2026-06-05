"""Testes do seed de dados de exemplo (`app.seed`)."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import PapelUsuarioEnum
from app.models.pedido import PedidoAjuda
from app.models.usuario import Usuario
from app.seed import semear


def test_semear_cria_registros_de_exemplo(db_session: Session) -> None:
    """O seed popula usuários, pedidos e atendimentos de exemplo."""
    resumo = semear(db_session)

    total_usuarios = db_session.scalar(select(func.count()).select_from(Usuario))
    total_pedidos = db_session.scalar(select(func.count()).select_from(PedidoAjuda))

    assert total_usuarios >= 2
    assert total_pedidos >= 1
    assert resumo["usuarios"] >= 2
    assert resumo["pedidos"] >= 1
    assert resumo["atendimentos"] >= 1


def test_semear_cria_um_admin(db_session: Session) -> None:
    """O seed cria ao menos um usuário com papel ADMIN."""
    semear(db_session)

    admins = db_session.scalars(
        select(Usuario).where(Usuario.papel == PapelUsuarioEnum.ADMIN)
    ).all()

    assert len(admins) >= 1


def test_semear_e_idempotente(db_session: Session) -> None:
    """Rodar o seed duas vezes não duplica registros."""
    semear(db_session)
    total_usuarios_1 = db_session.scalar(select(func.count()).select_from(Usuario))
    total_pedidos_1 = db_session.scalar(select(func.count()).select_from(PedidoAjuda))

    resumo_2 = semear(db_session)
    total_usuarios_2 = db_session.scalar(select(func.count()).select_from(Usuario))
    total_pedidos_2 = db_session.scalar(select(func.count()).select_from(PedidoAjuda))

    assert total_usuarios_2 == total_usuarios_1
    assert total_pedidos_2 == total_pedidos_1
    # Nada novo é criado na segunda passagem.
    assert resumo_2["usuarios"] == 0
    assert resumo_2["pedidos"] == 0
    assert resumo_2["atendimentos"] == 0
