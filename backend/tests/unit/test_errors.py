"""Testes da serialização de ProblemDetail e dos handlers de exceção."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.errors import (
    InvalidStatusTransitionError,
    PedidoNotFoundError,
    ProblemDetail,
    register_exception_handlers,
)


def test_problem_detail_serializa_campos_padrao() -> None:
    """`ProblemDetail` produz JSON com todos os campos RFC 7807."""
    p = ProblemDetail(title="X", status=400, detail="d")
    dump = p.model_dump()
    assert dump["type"] == "about:blank"
    assert dump["title"] == "X"
    assert dump["status"] == 400
    assert dump["detail"] == "d"
    assert dump["instance"] is None


def _make_test_app() -> FastAPI:
    """Cria uma mini-app FastAPI só para exercitar os handlers."""
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/raise-not-found")
    def raise_not_found() -> None:
        raise PedidoNotFoundError("id 42 não existe")

    @app.get("/raise-conflict")
    def raise_conflict() -> None:
        raise InvalidStatusTransitionError("aberto -> aberto é no-op")

    @app.get("/raise-http-error")
    def raise_http_error() -> None:
        from fastapi import HTTPException

        raise HTTPException(status_code=418, detail="sou um bule de chá")

    @app.post("/needs-int")
    def needs_int(value: int) -> dict[str, int]:
        return {"value": value}

    return app


def test_handler_traduz_pedido_not_found_para_404_problem_json() -> None:
    """`PedidoNotFoundError` vira 404 com media-type `application/problem+json`."""
    client = TestClient(_make_test_app())
    r = client.get("/raise-not-found")

    assert r.status_code == 404
    assert r.headers["content-type"] == "application/problem+json"
    body = r.json()
    assert body["title"] == "Pedido não encontrado"
    assert body["detail"] == "id 42 não existe"
    assert body["status"] == 404
    assert body["instance"] == "/raise-not-found"


def test_handler_traduz_transicao_invalida_para_409() -> None:
    """`InvalidStatusTransitionError` vira 409."""
    client = TestClient(_make_test_app())
    r = client.get("/raise-conflict")

    assert r.status_code == 409
    body = r.json()
    assert body["title"] == "Transição de status inválida"


def test_handler_traduz_http_exception_padrao() -> None:
    """`HTTPException` padrão também é traduzida para ProblemDetail."""
    client = TestClient(_make_test_app())
    r = client.get("/raise-http-error")

    assert r.status_code == 418
    body = r.json()
    assert body["status"] == 418
    assert body["detail"] == "sou um bule de chá"


def test_handler_traduz_validation_error_para_422() -> None:
    """Erros de validação Pydantic viram 422 ProblemDetail com detalhe legível."""
    client = TestClient(_make_test_app())
    r = client.post("/needs-int?value=nao-eh-int")

    assert r.status_code == 422
    body = r.json()
    assert body["title"] == "Erro de validação"
    assert "value" in body["detail"]
