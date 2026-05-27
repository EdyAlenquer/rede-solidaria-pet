"""Testes das configurações tipadas da aplicação."""

from app.config import Settings


def test_allowed_cors_origins_remove_espacos_e_valores_vazios() -> None:
    """`allowed_cors_origins` normaliza lista separada por vírgulas."""
    settings = Settings(cors_origins=" https://app.example.com, http://localhost:5173, ")

    assert settings.allowed_cors_origins() == [
        "https://app.example.com",
        "http://localhost:5173",
    ]
