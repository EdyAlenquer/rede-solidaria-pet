"""Re-exporta os schemas Pydantic do domínio."""

from app.schemas.atendimento import AtendimentoCreate, AtendimentoPublicRead, AtendimentoRead
from app.schemas.denuncia import DenunciaCreate, DenunciaRead
from app.schemas.doador import DoadorCreate, DoadorPublic, DoadorRead, DoadorUpdate
from app.schemas.estatistica import EstatisticasRead
from app.schemas.imagem import ImagemRead
from app.schemas.pagination import PageInfo, PedidoPage
from app.schemas.pedido import (
    PedidoContato,
    PedidoCreate,
    PedidoMeuRead,
    PedidoRead,
    PedidoStatusUpdate,
    PedidoUpdate,
)
from app.schemas.usuario import (
    LoginRequest,
    MeusDadosRead,
    TokenResponse,
    UsuarioCreate,
    UsuarioRead,
)

__all__ = [
    "AtendimentoCreate",
    "AtendimentoPublicRead",
    "AtendimentoRead",
    "DenunciaCreate",
    "DenunciaRead",
    "DoadorCreate",
    "DoadorPublic",
    "DoadorRead",
    "DoadorUpdate",
    "EstatisticasRead",
    "ImagemRead",
    "LoginRequest",
    "MeusDadosRead",
    "PageInfo",
    "PedidoContato",
    "PedidoCreate",
    "PedidoMeuRead",
    "PedidoPage",
    "PedidoRead",
    "PedidoStatusUpdate",
    "PedidoUpdate",
    "TokenResponse",
    "UsuarioCreate",
    "UsuarioRead",
]
