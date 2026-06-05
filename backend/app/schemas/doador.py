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
    """Payload para criação de doador.

    Exige o aceite explícito do termo de consentimento LGPD
    (`consentimento_aceito=True`).
    """

    consentimento_aceito: bool = False
    consentimento_versao: str | None = Field(default=None, max_length=20)

    @model_validator(mode="after")
    def _exige_consentimento(self) -> "DoadorCreate":
        """Garante que o termo de consentimento foi aceito.

        Returns:
            A própria instância validada.

        Raises:
            ValueError: se `consentimento_aceito` não for True.
        """
        if not self.consentimento_aceito:
            raise ValueError(
                "É necessário aceitar o termo de consentimento para cadastrar o doador."
            )
        return self


class DoadorUpdate(BaseModel):
    """Payload para atualização parcial de doador."""

    nome: str | None = Field(default=None, min_length=2, max_length=120)
    telefone: str | None = Field(default=None, max_length=40)
    email: EmailStr | None = None


class DoadorRead(BaseModel):
    """Schema de leitura administrativo — expõe o contato completo do doador.

    Servido apenas em rotas restritas a administradores; em contextos públicos
    use `DoadorPublic`, que omite telefone e email.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    telefone: str | None
    email: EmailStr | None


class DoadorPublic(BaseModel):
    """Schema público de doador — expõe apenas id e nome, sem contato."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
