"""Modelo ORM do doador/voluntário."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DoadorVoluntario(Base):
    """Doador ou voluntário que pode registrar atendimentos.

    Atributos:
        id: chave primária.
        nome: nome do doador/voluntário.
        telefone: telefone de contato (opcional).
        email: e-mail de contato (opcional, único quando informado).
        created_at: timestamp de criação (UTC, default agora).
        updated_at: timestamp da última alteração (UTC).
        deleted_at: timestamp de soft-delete; `None` enquanto ativo.
        consentimento_aceito: aceite explícito do termo LGPD (default False).
        consentimento_versao: versão do termo aceito (opcional).
        consentimento_em: instante do aceite (opcional).
        atendimentos: atendimentos realizados por este doador.

    A regra "pelo menos um entre telefone e email" é imposta tanto no schema
    quanto no banco, via `CheckConstraint`. O email, quando informado, é único.
    """

    __tablename__ = "doadores"
    __table_args__ = (
        CheckConstraint(
            "telefone IS NOT NULL OR email IS NOT NULL",
            name="ck_doadores_contato_obrigatorio",
        ),
        UniqueConstraint("email", name="uq_doadores_email"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    telefone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    email: Mapped[str | None] = mapped_column(String(120), nullable=True)
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

    # Consentimento LGPD
    consentimento_aceito: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("0")
    )
    consentimento_versao: Mapped[str | None] = mapped_column(String(20), nullable=True)
    consentimento_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    atendimentos: Mapped[list["AtendimentoPedido"]] = relationship(  # noqa: F821
        back_populates="doador",
        lazy="selectin",
    )
