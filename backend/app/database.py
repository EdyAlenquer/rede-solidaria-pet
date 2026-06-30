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


def _build_engine(database_url: str) -> Engine:
    """Cria um engine SQLAlchemy a partir de uma URL de banco.

    Habilita `pool_pre_ping` em todos os backends: o pre-ping testa a conexão
    antes de entregá-la e reconecta de forma transparente se ela estiver morta.
    É essencial para Postgres serverless que hiberna por ociosidade (ex.: Neon
    faz scale-to-zero após alguns minutos) — sem ele, a primeira requisição
    após a hibernação pega uma conexão derrubada e estoura. É inócuo no SQLite.

    Args:
        database_url: URL SQLAlchemy (já normalizada ou não) do banco alvo.

    Returns:
        Engine SQLAlchemy configurado.
    """
    normalized_url = _database_url_for_engine(database_url)
    connect_args = {"check_same_thread": False} if normalized_url.startswith("sqlite") else {}
    new_engine = create_engine(
        normalized_url,
        connect_args=connect_args,
        pool_pre_ping=True,
        future=True,
    )
    _register_sqlite_fk_pragma(new_engine)
    return new_engine


def _create_engine_from_settings():
    """Cria o engine usando a `database_url` corrente das Settings.

    Returns:
        Engine SQLAlchemy configurado.
    """
    return _build_engine(get_settings().database_url)


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
