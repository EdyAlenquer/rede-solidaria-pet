"""Modelo ORM do atendimento a um pedido."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.doador import DoadorVoluntario
from app.models.pedido import PedidoAjuda


class AtendimentoPedido(Base):
    """Registro de atendimento de um doador a um pedido.

    Atributos:
        id: chave primária.
        pedido_id: FK para o pedido atendido.
        doador_id: FK para o doador que atendeu.
        data_contato: quando o atendimento ocorreu (UTC, default agora).
        tipo_ajuda: descrição curta do tipo de ajuda oferecida.
        observacao: notas livres opcionais.
        updated_at: timestamp da última alteração (UTC).
        deleted_at: timestamp de soft-delete; `None` enquanto ativo.
        pedido: relação para o pedido.
        doador: relação para o doador.

    Um doador pode registrar no máximo um atendimento por pedido — garantido
    pela `UniqueConstraint(pedido_id, doador_id)`.
    """

    __tablename__ = "atendimentos"
    __table_args__ = (
        UniqueConstraint("pedido_id", "doador_id", name="uq_atendimentos_pedido_doador"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    pedido_id: Mapped[int] = mapped_column(
        ForeignKey("pedidos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    doador_id: Mapped[int] = mapped_column(
        ForeignKey("doadores.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    data_contato: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    tipo_ajuda: Mapped[str] = mapped_column(String(80), nullable=False)
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    pedido: Mapped[PedidoAjuda] = relationship(back_populates="atendimentos")
    doador: Mapped[DoadorVoluntario] = relationship(back_populates="atendimentos")
