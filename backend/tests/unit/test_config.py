"""Testes das configurações tipadas da aplicação."""

import pytest

from app.config import DEFAULT_SECRET_KEY, Settings


def test_allowed_cors_origins_em_producao_vem_apenas_do_env() -> None:
    """Em produção, as origens vêm exclusivamente de `CORS_ORIGINS` (sem default embutido)."""
    sem_env = Settings(app_env="production", cors_origins="")
    assert sem_env.allowed_cors_origins() == []

    com_env = Settings(
        app_env="production",
        cors_origins="https://frontend-edyalenquers-projects.vercel.app",
    )
    assert com_env.allowed_cors_origins() == ["https://frontend-edyalenquers-projects.vercel.app"]


def test_allowed_cors_origins_remove_espacos_e_valores_vazios() -> None:
    """`allowed_cors_origins` normaliza lista separada por vírgulas."""
    settings = Settings(cors_origins=" https://app.example.com, http://localhost:5173, ")

    assert settings.allowed_cors_origins() == [
        "https://app.example.com",
        "http://localhost:5173",
    ]


def test_defaults_de_jwt() -> None:
    """As Settings expõem defaults seguros de desenvolvimento para JWT."""
    settings = Settings()

    assert settings.secret_key == DEFAULT_SECRET_KEY
    assert settings.jwt_algorithm == "HS256"
    assert settings.access_token_expire_minutes == 60 * 24


def test_defaults_de_rate_limit(monkeypatch) -> None:
    """As Settings expõem defaults generosos e habilitados para rate limiting."""
    # A suíte desativa o rate limiting via env var; aqui validamos o default do
    # campo limpando a variável de ambiente.
    monkeypatch.delenv("RATE_LIMIT_ENABLED", raising=False)
    settings = Settings()

    assert settings.rate_limit_enabled is True
    assert settings.rate_limit_auth == "5/minute"
    assert settings.rate_limit_create == "30/minute"
    assert settings.rate_limit_contato == "30/minute"


def test_secret_key_efetiva_em_dev_usa_default() -> None:
    """Em desenvolvimento, `secret_key_efetiva` aceita o default inseguro."""
    settings = Settings(app_env="development", secret_key=DEFAULT_SECRET_KEY)

    assert settings.secret_key_efetiva() == DEFAULT_SECRET_KEY


def test_secret_key_efetiva_em_producao_com_default_falha() -> None:
    """Em produção, usar o `secret_key` default insegura levanta erro claro."""
    settings = Settings(app_env="production", secret_key=DEFAULT_SECRET_KEY)

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        settings.secret_key_efetiva()


def test_secret_key_efetiva_em_producao_com_chave_propria_ok() -> None:
    """Em produção, uma `secret_key` customizada é aceita."""
    settings = Settings(app_env="production", secret_key="uma-chave-bem-secreta-e-unica")

    assert settings.secret_key_efetiva() == "uma-chave-bem-secreta-e-unica"
