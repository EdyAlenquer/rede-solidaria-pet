"""Schemas Pydantic para as estatísticas públicas."""

from pydantic import BaseModel, ConfigDict, Field


class EstatisticasRead(BaseModel):
    """Contadores agregados expostos no dashboard público."""

    model_config = ConfigDict(from_attributes=True)

    total_pedidos: int = Field(ge=0)
    pedidos_abertos: int = Field(ge=0)
    pedidos_concluidos: int = Field(ge=0)
    total_atendimentos: int = Field(ge=0)
    total_cidades: int = Field(ge=0)
