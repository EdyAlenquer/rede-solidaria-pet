"""Configurações compartilhadas de pytest."""

import os
from collections.abc import Iterator

# Desativa o rate limiting para a suíte geral antes de importar a aplicação
# (a `app` singleton é construída no import de `app.main`). Testes específicos
# de 429 criam uma app própria com o limite habilitado via override.
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, event  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.database import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402


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


#: Credenciais do usuário registrado pelas fixtures de autenticação dos testes.
_USUARIO_TESTE = {
    "nome": "Usuário de Teste",
    "email": "teste@example.com",
    "senha": "senha-de-teste-123",
    "consentimento_aceito": True,
}


@pytest.fixture
def usuario_autenticado(api_client: TestClient) -> dict:
    """Registra um usuário de teste e retorna o corpo de `UsuarioRead`.

    Args:
        api_client: cliente HTTP ligado à sessão de teste.

    Returns:
        Dicionário com os dados públicos do usuário registrado (id, nome, email,
        papel).
    """
    resposta = api_client.post("/api/v1/auth/registro", json=_USUARIO_TESTE)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


@pytest.fixture
def auth_headers(api_client: TestClient, usuario_autenticado: dict) -> dict[str, str]:
    """Loga o usuário de teste e devolve o header `Authorization` com o Bearer.

    Depende de `usuario_autenticado` para garantir que a conta exista antes do
    login.

    Args:
        api_client: cliente HTTP ligado à sessão de teste.
        usuario_autenticado: usuário previamente registrado.

    Returns:
        Cabeçalho HTTP `{"Authorization": "Bearer <token>"}`.
    """
    resposta = api_client.post(
        "/api/v1/auth/login",
        json={"email": _USUARIO_TESTE["email"], "senha": _USUARIO_TESTE["senha"]},
    )
    assert resposta.status_code == 200, resposta.text
    token = resposta.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


#: Credenciais de um segundo usuário (não autor), usado para testar autorização.
_OUTRO_USUARIO = {
    "nome": "Outro Usuário",
    "email": "outro@example.com",
    "senha": "outra-senha-de-teste-123",
    "consentimento_aceito": True,
}

#: Credenciais do usuário promovido a admin nas fixtures de autorização.
_ADMIN_USUARIO = {
    "nome": "Admin de Teste",
    "email": "admin@example.com",
    "senha": "senha-admin-de-teste-123",
    "consentimento_aceito": True,
}


@pytest.fixture
def auth_headers_outro(api_client: TestClient) -> dict[str, str]:
    """Registra e loga um segundo usuário (não autor) e devolve seu Bearer.

    Útil para validar que apenas o autor (ou admin) edita/remove um pedido.

    Args:
        api_client: cliente HTTP ligado à sessão de teste.

    Returns:
        Cabeçalho HTTP `{"Authorization": "Bearer <token>"}` do outro usuário.
    """
    registro = api_client.post("/api/v1/auth/registro", json=_OUTRO_USUARIO)
    assert registro.status_code == 201, registro.text
    login = api_client.post(
        "/api/v1/auth/login",
        json={"email": _OUTRO_USUARIO["email"], "senha": _OUTRO_USUARIO["senha"]},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.fixture
def admin_headers(api_client: TestClient, db_session: Session) -> dict[str, str]:
    """Registra um usuário, promove-o a admin no banco e devolve seu Bearer.

    Como não há endpoint público de promoção, o papel é ajustado direto na
    sessão de teste após o registro.

    Args:
        api_client: cliente HTTP ligado à sessão de teste.
        db_session: sessão usada para promover o usuário a admin.

    Returns:
        Cabeçalho HTTP `{"Authorization": "Bearer <token>"}` de um admin.
    """
    from app.models.enums import PapelUsuarioEnum
    from app.models.usuario import Usuario

    registro = api_client.post("/api/v1/auth/registro", json=_ADMIN_USUARIO)
    assert registro.status_code == 201, registro.text

    usuario = db_session.get(Usuario, registro.json()["id"])
    usuario.papel = PapelUsuarioEnum.ADMIN
    db_session.commit()

    login = api_client.post(
        "/api/v1/auth/login",
        json={"email": _ADMIN_USUARIO["email"], "senha": _ADMIN_USUARIO["senha"]},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}
