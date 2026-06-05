"""Schemas Pydantic para ImagemPedido."""

from pydantic import BaseModel, ConfigDict, Field


class ImagemRead(BaseModel):
    """Schema de leitura de uma imagem da galeria do pedido.

    Atributos:
        id: identificador da imagem.
        url: endereço público da imagem.
        ordem: posição de exibição na galeria (menor primeiro).
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str = Field(max_length=500)
    ordem: int = Field(default=0, ge=0)
