"""Re-exporta os repositórios."""

from app.repositories.atendimento_repository import AtendimentoRepository
from app.repositories.denuncia_repository import DenunciaRepository
from app.repositories.doador_repository import DoadorRepository
from app.repositories.estatistica_repository import EstatisticaRepository
from app.repositories.pedido_repository import PedidoRepository

__all__ = [
    "AtendimentoRepository",
    "DenunciaRepository",
    "DoadorRepository",
    "EstatisticaRepository",
    "PedidoRepository",
]
