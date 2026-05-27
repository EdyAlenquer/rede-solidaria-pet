"""Testes da configuração Alembic."""

from app.database import _database_url_for_engine


def test_alembic_env_reusa_normalizacao_de_url_do_runtime() -> None:
    """Alembic deve usar o mesmo driver PostgreSQL do runtime."""
    raw_url = "postgresql://user:pass@host:5432/db"

    assert _database_url_for_engine(raw_url) == "postgresql+psycopg://user:pass@host:5432/db"
