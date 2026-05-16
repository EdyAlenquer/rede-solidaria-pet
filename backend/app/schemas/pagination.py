"""Schemas de paginação para listagens."""

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.pedido import PedidoRead


class PageInfo(BaseModel):
    """Metadados de paginação retornados em listagens."""

    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)
    total_pages: int = Field(ge=0)


class PedidoPage(BaseModel):
    """Página de PedidoRead com metadados de paginação."""

    model_config = ConfigDict(from_attributes=True)

    items: list[PedidoRead]
    page_info: PageInfo
