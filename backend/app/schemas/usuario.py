"""Schemas Pydantic para usuários e autenticação."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.models.enums import PapelUsuarioEnum
from app.schemas.atendimento import AtendimentoRead
from app.schemas.pedido import PedidoMeuRead


class UsuarioCreate(BaseModel):
    """Payload de registro de um novo usuário.

    Exige o aceite explícito do termo de consentimento LGPD
    (`consentimento_aceito=True`) e uma senha com no mínimo 8 caracteres.
    """

    nome: str = Field(min_length=2, max_length=120)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=128)
    telefone: str | None = Field(default=None, max_length=40)
    consentimento_aceito: bool = False
    consentimento_versao: str | None = Field(default=None, max_length=20)

    @model_validator(mode="after")
    def _exige_consentimento(self) -> "UsuarioCreate":
        """Garante que o termo de consentimento foi aceito.

        Returns:
            A própria instância validada.

        Raises:
            ValueError: se `consentimento_aceito` não for True.
        """
        if not self.consentimento_aceito:
            raise ValueError("É necessário aceitar o termo de consentimento para criar a conta.")
        return self


class UsuarioRead(BaseModel):
    """Schema de leitura de usuário — nunca expõe a senha nem o hash."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: EmailStr
    papel: PapelUsuarioEnum


class MeusDadosRead(BaseModel):
    """Exportação dos dados pessoais do usuário atual (direito de acesso LGPD).

    Reúne, em uma estrutura única e documentada, tudo o que a plataforma guarda
    sobre o titular: seu perfil, os pedidos que criou (incluindo o `contato`
    próprio) e os atendimentos que registrou.
    """

    perfil: UsuarioRead
    pedidos: list[PedidoMeuRead] = Field(default_factory=list)
    atendimentos: list[AtendimentoRead] = Field(default_factory=list)


class LoginRequest(BaseModel):
    """Payload de login com credenciais de e-mail e senha."""

    email: EmailStr
    senha: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    """Resposta de autenticação contendo o access token JWT."""

    access_token: str
    token_type: str = "bearer"
