"""Modelo ORM de denúncia de um pedido (moderação)."""

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import MotivoDenunciaEnum, StatusDenunciaEnum


class Denuncia(Base):
    """Denúncia de um pedido registrada por um usuário autenticado.

    Atributos:
        id: chave primária.
        pedido_id: FK para o pedido denunciado (CASCADE no delete).
        autor_id: FK nullable para o usuário denunciante (`usuarios.id`); fica
            ``NULL`` se o usuário for removido (ON DELETE SET NULL).
        motivo: motivo declarado da denúncia (enum `motivo_denuncia_enum`).
        descricao: detalhamento livre opcional.
        status: estado de tratamento (default `ABERTA`).
        criado_em: timestamp de criação (UTC, default agora).
    """

    __tablename__ = "denuncias"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    pedido_id: Mapped[int] = mapped_column(
        ForeignKey("pedidos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    autor_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    motivo: Mapped[MotivoDenunciaEnum] = mapped_column(
        Enum(MotivoDenunciaEnum, name="motivo_denuncia_enum"), nullable=False
    )
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[StatusDenunciaEnum] = mapped_column(
        Enum(StatusDenunciaEnum, name="status_denuncia_enum"),
        nullable=False,
        default=StatusDenunciaEnum.ABERTA,
        server_default=StatusDenunciaEnum.ABERTA.name,
        index=True,
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
