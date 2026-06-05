"""Testes de validação dos schemas de usuário e autenticação."""

import pytest
from pydantic import ValidationError

from app.models.enums import PapelUsuarioEnum
from app.schemas import LoginRequest, TokenResponse, UsuarioCreate, UsuarioRead

_USUARIO_VALIDO = {
    "nome": "Ana Protetora",
    "email": "ana@example.com",
    "senha": "senha-com-8+",
    "consentimento_aceito": True,
}


def test_usuario_create_aceita_payload_valido() -> None:
    """UsuarioCreate aceita um payload completo e válido."""
    u = UsuarioCreate(**_USUARIO_VALIDO)

    assert u.email == "ana@example.com"
    assert u.senha == "senha-com-8+"
    assert u.consentimento_aceito is True


def test_usuario_create_rejeita_senha_curta() -> None:
    """Senha com menos de 8 caracteres é rejeitada."""
    with pytest.raises(ValidationError):
        UsuarioCreate(**{**_USUARIO_VALIDO, "senha": "1234567"})


def test_usuario_create_rejeita_email_invalido() -> None:
    """Email malformado é rejeitado."""
    with pytest.raises(ValidationError):
        UsuarioCreate(**{**_USUARIO_VALIDO, "email": "nao-e-email"})


def test_usuario_create_exige_consentimento() -> None:
    """Sem aceite do consentimento LGPD, a criação é rejeitada."""
    with pytest.raises(ValidationError):
        UsuarioCreate(**{**_USUARIO_VALIDO, "consentimento_aceito": False})


def test_usuario_read_nao_expoe_senha_hash() -> None:
    """UsuarioRead não inclui o campo `senha_hash`."""
    campos = set(UsuarioRead.model_fields)

    assert "senha_hash" not in campos
    assert "senha" not in campos
    assert campos == {"id", "nome", "email", "papel"}


def test_usuario_read_serializa_a_partir_de_objeto() -> None:
    """UsuarioRead lê atributos de um objeto (from_attributes)."""

    class _Fake:
        id = 1
        nome = "Ana"
        email = "ana@example.com"
        papel = PapelUsuarioEnum.PROTETOR
        senha_hash = "$argon2id$segredo"

    lido = UsuarioRead.model_validate(_Fake())

    assert lido.id == 1
    assert lido.papel is PapelUsuarioEnum.PROTETOR


def test_login_request_valida_email() -> None:
    """LoginRequest exige email válido e senha."""
    req = LoginRequest(email="ana@example.com", senha="qualquer")

    assert req.email == "ana@example.com"
    assert req.senha == "qualquer"


def test_token_response_token_type_default_bearer() -> None:
    """TokenResponse usa `token_type=bearer` por padrão."""
    resp = TokenResponse(access_token="abc.def.ghi")

    assert resp.access_token == "abc.def.ghi"
    assert resp.token_type == "bearer"
