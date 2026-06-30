"""Modelo ORM de imagem associada a um pedido de ajuda."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ImagemPedido(Base):
    """Imagem vinculada a um pedido de ajuda.

    O upload do arquivo é feito pela camada de serviço através do
    `StorageBackend` (disco local em dev, object storage S3/R2 em produção);
    este modelo persiste a URL pública resultante e a ordenação para exibição
    na galeria do pedido.

    Atributos:
        id: chave primária.
        pedido_id: FK para o pedido dono da imagem (CASCADE no delete).
        url: endereço público da imagem (até 500 caracteres).
        ordem: posição de exibição na galeria (menor primeiro, default 0).
        criado_em: timestamp de criação (UTC, default agora).
        pedido: relação inversa para o pedido dono.
    """

    __tablename__ = "imagens_pedido"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    pedido_id: Mapped[int] = mapped_column(
        ForeignKey("pedidos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    ordem: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    pedido: Mapped["PedidoAjuda"] = relationship(back_populates="imagens")  # noqa: F821
