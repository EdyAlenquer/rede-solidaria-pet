"""Configuração do SQLAlchemy: engine, Base declarativa, sessão e dependência."""

from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    """Base declarativa compartilhada por todos os modelos ORM."""


def _register_sqlite_fk_pragma(target_engine: Engine) -> None:
    """Ativa `PRAGMA foreign_keys=ON` em conexões SQLite do engine.

    Garante paridade dev/test/prod no enforcement de chaves estrangeiras:
    o SQLite, por padrão, não impõe FKs sem este pragma. Em outros bancos
    (ex.: Postgres) é no-op, pois o listener só é registrado para SQLite.

    Args:
        target_engine: engine SQLAlchemy a instrumentar.

    Side Effects:
        Registra um listener `connect` no engine quando o backend é SQLite.
    """
    if target_engine.url.get_backend_name() != "sqlite":
        return

    @event.listens_for(target_engine, "connect")
    def _enable_sqlite_fk(dbapi_conn, connection_record) -> None:  # noqa: ARG001
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


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
    new_engine = create_engine(database_url, connect_args=connect_args, future=True)
    _register_sqlite_fk_pragma(new_engine)
    return new_engine


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
