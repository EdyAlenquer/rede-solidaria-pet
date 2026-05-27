"""Configuração do SQLAlchemy: engine, Base declarativa, sessão e dependência."""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    """Base declarativa compartilhada por todos os modelos ORM."""


def _database_url_for_engine(database_url: str) -> str:
    """Normaliza a URL de banco para o driver instalado.

    Args:
        database_url: URL SQLAlchemy recebida por configuração.

    Returns:
        URL compatível com o driver instalado para uso no `create_engine`.
    """
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


def _create_engine_from_settings():
    """Cria o engine usando a `database_url` corrente das Settings.

    Returns:
        Engine SQLAlchemy configurado.
    """
    settings = get_settings()
    database_url = _database_url_for_engine(settings.database_url)
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args, future=True)


engine = _create_engine_from_settings()

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def get_db() -> Iterator[Session]:
    """Dependência FastAPI que fornece uma `Session` por request.

    Yields:
        Sessão SQLAlchemy abinda aberta; é fechada ao final do request.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
