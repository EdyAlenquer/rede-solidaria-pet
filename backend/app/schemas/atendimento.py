"""Schemas Pydantic para AtendimentoPedido."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AtendimentoBase(BaseModel):
    """Campos comuns aos schemas de entrada de atendimento."""

    tipo_ajuda: str = Field(min_length=2, max_length=80)
    observacao: str | None = None


class AtendimentoCreate(AtendimentoBase):
    """Payload para registrar um atendimento.

    `doador_id` é informado no corpo; `pedido_id` vem da URL.
    """

    doador_id: int = Field(gt=0)


class AtendimentoRead(AtendimentoBase):
    """Schema de leitura de atendimento."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    pedido_id: int
    doador_id: int
    data_contato: datetime
