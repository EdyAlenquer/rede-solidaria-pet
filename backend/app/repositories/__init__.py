"""Re-exporta os repositórios."""

from app.repositories.doador_repository import DoadorRepository
from app.repositories.pedido_repository import PedidoRepository

__all__ = ["DoadorRepository", "PedidoRepository"]
