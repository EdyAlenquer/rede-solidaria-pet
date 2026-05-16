"""Schemas Pydantic para DoadorVoluntario."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class DoadorBase(BaseModel):
    """Campos comuns aos schemas de entrada de doador."""

    nome: str = Field(min_length=2, max_length=120)
    telefone: str | None = Field(default=None, max_length=40)
    email: EmailStr | None = None

    @model_validator(mode="after")
    def _exige_telefone_ou_email(self) -> "DoadorBase":
        """Garante que ao menos um contato (telefone ou email) foi informado."""
        if not self.telefone and not self.email:
            raise ValueError("Informe ao menos um contato: telefone ou email.")
        return self


class DoadorCreate(DoadorBase):
    """Payload para criação de doador."""


class DoadorUpdate(BaseModel):
    """Payload para atualização parcial de doador."""

    nome: str | None = Field(default=None, min_length=2, max_length=120)
    telefone: str | None = Field(default=None, max_length=40)
    email: EmailStr | None = None


class DoadorRead(BaseModel):
    """Schema de leitura — usado internamente; em rotas públicas usar `DoadorPublic`."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    telefone: str | None
    email: EmailStr | None
