"""Configurações compartilhadas de pytest."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import get_db
from app.main import app
from app.models import Base


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Fornece um TestClient da aplicação FastAPI sem overrides.

    Yields:
        Cliente HTTP de teste apontando para a aplicação principal.
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db_session() -> Iterator[Session]:
    """Fornece uma sessão SQLAlchemy ligada a um SQLite em memória.

    Cria todas as tabelas antes do teste e descarta tudo após.
    Ativa o pragma `foreign_keys=ON` em cada conexão.

    Yields:
        Sessão SQLAlchemy nova e isolada.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )

    @event.listens_for(engine, "connect")
    def _enable_sqlite_fk(dbapi_conn, connection_record) -> None:  # noqa: ARG001
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def api_client(db_session: Session) -> Iterator[TestClient]:
    """TestClient com `get_db` overridado para usar a `db_session` de teste.

    Yields:
        Cliente HTTP onde toda dependência `get_db` rende a sessão de teste.
    """

    def _override_get_db() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
