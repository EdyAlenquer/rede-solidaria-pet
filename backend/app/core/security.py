"""Primitivas de segurança: hash de senha (argon2) e tokens JWT (HS256)."""

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import Argon2Error, VerifyMismatchError

from app.config import get_settings

#: Hasher argon2 compartilhado; é stateless e seguro para reuso entre chamadas.
_password_hasher = PasswordHasher()


class TokenInvalidoError(Exception):
    """Erro levantado quando um token JWT é inválido, expirado ou malformado."""


def hash_senha(senha: str) -> str:
    """Gera o hash argon2 de uma senha em texto puro.

    Args:
        senha: senha em texto puro fornecida pelo usuário.

    Returns:
        Hash argon2 codificado (prefixo ``$argon2``), seguro para persistir.
    """
    return _password_hasher.hash(senha)


def verificar_senha(senha: str, senha_hash: str) -> bool:
    """Verifica se uma senha em texto puro corresponde ao hash armazenado.

    Args:
        senha: senha em texto puro a verificar.
        senha_hash: hash argon2 previamente armazenado.

    Returns:
        True se a senha corresponder ao hash; False caso contrário (inclusive
        quando o hash é inválido/corrompido).
    """
    try:
        return _password_hasher.verify(senha_hash, senha)
    except VerifyMismatchError:
        return False
    except Argon2Error:
        return False


def criar_access_token(
    sub: str,
    *,
    extra: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """Cria um access token JWT assinado (HS256) para um subject.

    Args:
        sub: identificador do subject (tipicamente o id do usuário, como string).
        extra: claims adicionais a incluir no payload (ex.: ``{"papel": "admin"}``).
        expires_delta: validade do token; se omitido, usa
            ``access_token_expire_minutes`` das Settings.

    Returns:
        Token JWT codificado como string.

    Side Effects:
        Lê as Settings da aplicação para chave, algoritmo e expiração; em
        produção valida que a SECRET_KEY não é o default inseguro.
    """
    settings = get_settings()
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    agora = datetime.now(UTC)
    payload: dict[str, Any] = {"sub": sub, "iat": agora, "exp": agora + expires_delta}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.secret_key_efetiva(), algorithm=settings.jwt_algorithm)


def decodificar_token(token: str) -> dict[str, Any]:
    """Decodifica e valida um access token JWT.

    Args:
        token: token JWT recebido (sem o prefixo ``Bearer``).

    Returns:
        Payload do token como dicionário (inclui ``sub`` e ``exp``).

    Raises:
        TokenInvalidoError: se o token for malformado, expirado ou assinado com
            chave/algoritmo diferentes dos configurados.
    """
    settings = get_settings()
    try:
        return jwt.decode(
            token,
            settings.secret_key_efetiva(),
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.PyJWTError as exc:
        raise TokenInvalidoError("Token inválido ou expirado.") from exc
