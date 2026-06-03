"""Testes do módulo de segurança (hash de senha e tokens JWT)."""

from datetime import timedelta

import jwt
import pytest

from app.core.security import (
    TokenInvalidoError,
    criar_access_token,
    decodificar_token,
    hash_senha,
    verificar_senha,
)


def test_hash_senha_nao_armazena_texto_puro() -> None:
    """O hash gerado difere da senha original e tem formato argon2."""
    senha = "senha-super-secreta"

    digest = hash_senha(senha)

    assert digest != senha
    assert digest.startswith("$argon2")


def test_verificar_senha_aceita_senha_correta() -> None:
    """`verificar_senha` retorna True para a senha correta."""
    senha = "senha-super-secreta"
    digest = hash_senha(senha)

    assert verificar_senha(senha, digest) is True


def test_verificar_senha_rejeita_senha_incorreta() -> None:
    """`verificar_senha` retorna False para senha errada."""
    digest = hash_senha("senha-super-secreta")

    assert verificar_senha("outra-senha", digest) is False


def test_hashes_da_mesma_senha_sao_diferentes() -> None:
    """O argon2 usa salt aleatório: dois hashes da mesma senha diferem."""
    assert hash_senha("igual") != hash_senha("igual")


def test_criar_e_decodificar_token_round_trip() -> None:
    """Um token criado para um `sub` é decodificável e preserva o `sub`."""
    token = criar_access_token(sub="42")

    payload = decodificar_token(token)

    assert payload["sub"] == "42"
    assert "exp" in payload


def test_criar_access_token_inclui_claims_extras() -> None:
    """Claims extras informados são incorporados ao token."""
    token = criar_access_token(sub="7", extra={"papel": "admin"})

    payload = decodificar_token(token)

    assert payload["sub"] == "7"
    assert payload["papel"] == "admin"


def test_decodificar_token_invalido_levanta_erro() -> None:
    """Um token corrompido levanta `TokenInvalidoError`."""
    with pytest.raises(TokenInvalidoError):
        decodificar_token("isto.nao.e-um-token")


def test_decodificar_token_expirado_levanta_erro() -> None:
    """Um token expirado levanta `TokenInvalidoError`."""
    token = criar_access_token(sub="1", expires_delta=timedelta(minutes=-1))

    with pytest.raises(TokenInvalidoError):
        decodificar_token(token)


def test_token_assinado_com_outra_chave_e_rejeitado() -> None:
    """Um token assinado por outra chave não é aceito pela aplicação."""
    forjado = jwt.encode({"sub": "1"}, "chave-do-atacante", algorithm="HS256")

    with pytest.raises(TokenInvalidoError):
        decodificar_token(forjado)
