"""Modelo ORM do pedido de ajuda."""

from datetime import datetime

from sqlalchemy import DateTime, Enum, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import StatusPedidoEnum, UrgenciaEnum


class PedidoAjuda(Base):
    """Pedido público de ajuda criado por um protetor.

    Atributos:
        id: chave primária.
        titulo: título curto descritivo.
        descricao: detalhamento do pedido.
        categoria: tipo de ajuda (ração, transporte, abrigo, etc.).
        urgencia: nível de urgência declarado.
        status: estado no ciclo de vida (aberto/em_andamento/concluido).
        contato: forma de contato do responsável (telefone ou e-mail).
        data_criacao: timestamp de criação (UTC, default agora).
        atendimentos: atendimentos vinculados a este pedido.
    """

    __tablename__ = "pedidos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    titulo: Mapped[str] = mapped_column(String(120), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    categoria: Mapped[str] = mapped_column(String(60), nullable=False)
    urgencia: Mapped[UrgenciaEnum] = mapped_column(
        Enum(UrgenciaEnum, name="urgencia_enum"), nullable=False
    )
    status: Mapped[StatusPedidoEnum] = mapped_column(
        Enum(StatusPedidoEnum, name="status_pedido_enum"),
        nullable=False,
        default=StatusPedidoEnum.ABERTO,
    )
    contato: Mapped[str] = mapped_column(String(120), nullable=False)
    data_criacao: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    atendimentos: Mapped[list["AtendimentoPedido"]] = relationship(  # noqa: F821
        back_populates="pedido",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
