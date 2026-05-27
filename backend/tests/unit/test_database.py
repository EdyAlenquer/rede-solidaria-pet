"""Testes da configuração de banco e da dependência `get_db`."""

from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, _database_url_for_engine, engine, get_db


def test_engine_usa_sqlite_em_modo_dev() -> None:
    """O engine carregado pelas Settings deve ser SQLite no ambiente padrão."""
    assert "sqlite" in str(engine.url)


def test_database_url_for_engine_usa_psycopg3_para_postgres_render() -> None:
    """URL PostgreSQL sem driver explícito deve usar `psycopg` v3."""
    url = _database_url_for_engine("postgresql://user:pass@host:5432/db")

    assert url == "postgresql+psycopg://user:pass@host:5432/db"


def test_database_url_for_engine_preserva_driver_explicito() -> None:
    """URL PostgreSQL com driver explícito não deve ser reescrita."""
    url = _database_url_for_engine("postgresql+psycopg://user:pass@host:5432/db")

    assert url == "postgresql+psycopg://user:pass@host:5432/db"


def test_base_expoe_metadata_vazia_antes_de_modelos() -> None:
    """A `Base` está disponível e a metadata começa sem tabelas registradas."""
    assert hasattr(Base, "metadata")


def test_session_local_cria_sessao_funcional() -> None:
    """`SessionLocal()` retorna uma `Session` ativa e fechável."""
    session = SessionLocal()
    try:
        assert isinstance(session, Session)
    finally:
        session.close()


def test_get_db_abre_e_fecha_sessao() -> None:
    """`get_db` rende uma sessão e a fecha ao consumir o gerador."""
    gen = get_db()
    session = next(gen)
    assert isinstance(session, Session)
    gen.close()
