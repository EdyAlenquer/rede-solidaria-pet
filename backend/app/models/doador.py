"""Modelo ORM do doador/voluntário."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DoadorVoluntario(Base):
    """Doador ou voluntário que pode registrar atendimentos.

    Atributos:
        id: chave primária.
        nome: nome do doador/voluntário.
        telefone: telefone de contato (opcional).
        email: e-mail de contato (opcional).
        atendimentos: atendimentos realizados por este doador.

    Pelo menos um entre `telefone` e `email` deve ser preenchido
    (regra validada no schema, não no banco — SQLite não suporta CHECK
    com OR de forma trivial em todas as versões antigas).
    """

    __tablename__ = "doadores"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    telefone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    email: Mapped[str | None] = mapped_column(String(120), nullable=True)

    atendimentos: Mapped[list["AtendimentoPedido"]] = relationship(  # noqa: F821
        back_populates="doador",
        lazy="selectin",
    )
