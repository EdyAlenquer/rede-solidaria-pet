"""Re-exporta os schemas Pydantic do domínio."""

from app.schemas.atendimento import AtendimentoCreate, AtendimentoRead
from app.schemas.doador import DoadorCreate, DoadorRead, DoadorUpdate
from app.schemas.pagination import PageInfo, PedidoPage
from app.schemas.pedido import (
    PedidoCreate,
    PedidoRead,
    PedidoStatusUpdate,
    PedidoUpdate,
)

__all__ = [
    "AtendimentoCreate",
    "AtendimentoRead",
    "DoadorCreate",
    "DoadorRead",
    "DoadorUpdate",
    "PageInfo",
    "PedidoCreate",
    "PedidoPage",
    "PedidoRead",
    "PedidoStatusUpdate",
    "PedidoUpdate",
]
