"""Testes do modelo `Usuario` e da FK `pedidos.autor_id -> usuarios.id`."""

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.enums import PapelUsuarioEnum
from app.models.usuario import Usuario
from app.repositories.pedido_repository import PedidoRepository
from app.schemas import PedidoCreate


def _usuario(**overrides) -> Usuario:
    """Constrói um `Usuario` válido para os testes."""
    base = {
        "nome": "Ana Protetora",
        "email": "ana@example.com",
        "senha_hash": "$argon2id$fake",
    }
    base.update(overrides)
    return Usuario(**base)


def test_usuario_papel_default_protetor(db_session: Session) -> None:
    """Ao persistir sem papel explícito, o usuário fica como `PROTETOR`."""
    usuario = _usuario()
    db_session.add(usuario)
    db_session.commit()
    db_session.refresh(usuario)

    assert usuario.id is not None
    assert usuario.papel is PapelUsuarioEnum.PROTETOR


def test_usuario_email_unico(db_session: Session) -> None:
    """O banco rejeita dois usuários com o mesmo email (UniqueConstraint)."""
    db_session.add(_usuario(email="dup@example.com"))
    db_session.flush()
    db_session.add(_usuario(nome="Outro", email="dup@example.com"))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_pedido_autor_id_aceita_usuario_existente(db_session: Session) -> None:
    """`autor_id` referencia um usuário existente sem violar a FK."""
    usuario = _usuario()
    db_session.add(usuario)
    db_session.commit()

    repo = PedidoRepository(db_session)
    pedido = repo.create(
        PedidoCreate(
            titulo="Resgate",
            descricao="Descrição com tamanho suficiente para validar.",
            categoria="resgate",
            urgencia="alta",
            contato="11999990000",
            cidade="São Paulo",
            estado="SP",
            consentimento_aceito=True,
        ),
        autor_id=usuario.id,
    )

    assert pedido.autor_id == usuario.id


def test_pedido_autor_id_invalido_viola_fk(db_session: Session) -> None:
    """`autor_id` apontando para usuário inexistente viola a FK."""
    repo = PedidoRepository(db_session)
    with pytest.raises(IntegrityError):
        repo.create(
            PedidoCreate(
                titulo="Resgate",
                descricao="Descrição com tamanho suficiente para validar.",
                categoria="resgate",
                urgencia="alta",
                contato="11999990000",
                cidade="São Paulo",
                estado="SP",
                consentimento_aceito=True,
            ),
            autor_id=999999,
        )


def test_usuario_relationship_pedidos(db_session: Session) -> None:
    """O relationship `usuario.pedidos` agrega os pedidos de autoria."""
    usuario = _usuario()
    db_session.add(usuario)
    db_session.commit()

    repo = PedidoRepository(db_session)
    repo.create(
        PedidoCreate(
            titulo="Resgate",
            descricao="Descrição com tamanho suficiente para validar.",
            categoria="resgate",
            urgencia="alta",
            contato="11999990000",
            cidade="São Paulo",
            estado="SP",
            consentimento_aceito=True,
        ),
        autor_id=usuario.id,
    )
    db_session.refresh(usuario)

    assert len(usuario.pedidos) == 1
