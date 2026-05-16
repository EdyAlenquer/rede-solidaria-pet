"""Schemas Pydantic para PedidoAjuda."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import StatusPedidoEnum, UrgenciaEnum


class PedidoBase(BaseModel):
    """Campos comuns aos schemas de entrada de pedido."""

    titulo: str = Field(min_length=3, max_length=120)
    descricao: str = Field(min_length=10)
    categoria: str = Field(min_length=2, max_length=60)
    urgencia: UrgenciaEnum
    contato: str = Field(min_length=5, max_length=120)


class PedidoCreate(PedidoBase):
    """Payload para criação de um pedido (todos os campos obrigatórios)."""


class PedidoUpdate(BaseModel):
    """Payload para atualização parcial — campos opcionais.

    Exclui `status`, atualizado por endpoint dedicado.
    """

    titulo: str | None = Field(default=None, min_length=3, max_length=120)
    descricao: str | None = Field(default=None, min_length=10)
    categoria: str | None = Field(default=None, min_length=2, max_length=60)
    urgencia: UrgenciaEnum | None = None
    contato: str | None = Field(default=None, min_length=5, max_length=120)


class PedidoStatusUpdate(BaseModel):
    """Payload exclusivo para mudança de status."""

    status: StatusPedidoEnum


class PedidoRead(PedidoBase):
    """Schema de leitura — adiciona campos servidos pelo backend."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: StatusPedidoEnum
    data_criacao: datetime
