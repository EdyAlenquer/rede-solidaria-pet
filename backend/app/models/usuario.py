"""Modelo ORM do usuário autenticável (conta de protetor/admin)."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import PapelUsuarioEnum


class Usuario(Base):
    """Conta de usuário capaz de autenticar e ser autor de pedidos.

    Atributos:
        id: chave primária.
        nome: nome do usuário.
        email: e-mail de login (único, obrigatório, indexado).
        senha_hash: hash argon2 da senha (nunca a senha em texto puro).
        papel: papel do usuário no sistema (default `PROTETOR`).
        telefone: telefone de contato (opcional).
        consentimento_aceito: aceite explícito do termo LGPD (default False).
        consentimento_versao: versão do termo aceito (opcional).
        consentimento_em: instante do aceite (opcional).
        created_at: timestamp de criação (UTC, default agora).
        updated_at: timestamp da última alteração (UTC, atualizado a cada update).
        deleted_at: timestamp de soft-delete; `None` enquanto ativo.
        pedidos: pedidos dos quais este usuário é autor.
    """

    __tablename__ = "usuarios"
    __table_args__ = (UniqueConstraint("email", name="uq_usuarios_email"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    papel: Mapped[PapelUsuarioEnum] = mapped_column(
        Enum(PapelUsuarioEnum, name="papel_usuario_enum"),
        nullable=False,
        default=PapelUsuarioEnum.PROTETOR,
        server_default=PapelUsuarioEnum.PROTETOR.name,
    )
    telefone: Mapped[str | None] = mapped_column(String(40), nullable=True)

    # Consentimento LGPD
    consentimento_aceito: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("0")
    )
    consentimento_versao: Mapped[str | None] = mapped_column(String(20), nullable=True)
    consentimento_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    pedidos: Mapped[list["PedidoAjuda"]] = relationship(  # noqa: F821
        back_populates="autor",
        lazy="selectin",
    )
