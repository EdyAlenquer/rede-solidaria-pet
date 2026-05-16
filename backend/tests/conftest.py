"""Configurações compartilhadas de pytest."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Fornece um TestClient da aplicação FastAPI.

    Yields:
        Cliente HTTP de teste apontando para a aplicação principal.
    """
    with TestClient(app) as test_client:
        yield test_client
