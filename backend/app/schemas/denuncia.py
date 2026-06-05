"""Schemas Pydantic para Denuncia (moderação)."""

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import MotivoDenunciaEnum, StatusDenunciaEnum


class DenunciaCreate(BaseModel):
    """Payload para registrar uma denúncia de pedido.

    O `pedido_id` vem da URL e o autor é derivado do usuário autenticado.
    """

    motivo: MotivoDenunciaEnum
    descricao: str | None = Field(default=None, max_length=2000)


class DenunciaRead(BaseModel):
    """Schema de leitura de denúncia para uso administrativo.

    `criado_em` é normalizado para UTC-aware (o SQLite devolve timestamps sem
    offset), garantindo serialização ISO-8601 com offset.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    pedido_id: int
    autor_id: int | None
    motivo: MotivoDenunciaEnum
    descricao: str | None
    status: StatusDenunciaEnum
    criado_em: datetime

    @field_validator("criado_em")
    @classmethod
    def _normaliza_para_utc(cls, valor: datetime) -> datetime:
        """Garante offset explícito (UTC) em `criado_em`.

        Args:
            valor: timestamp lido do modelo (pode ser ingênuo no SQLite).

        Returns:
            Mesmo instante com `tzinfo` definido (UTC quando ausente).
        """
        if valor.tzinfo is None:
            return valor.replace(tzinfo=UTC)
        return valor
