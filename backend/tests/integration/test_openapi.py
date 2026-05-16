"""Testes de smoke da documentação OpenAPI gerada."""

from fastapi.testclient import TestClient


def test_openapi_json_lista_todos_endpoints_de_pedidos(client: TestClient) -> None:
    """`/openapi.json` inclui as 4 rotas de pedidos."""
    r = client.get("/openapi.json")
    assert r.status_code == 200

    paths = r.json()["paths"]

    assert "/api/v1/pedidos" in paths
    assert "post" in paths["/api/v1/pedidos"]
    assert "get" in paths["/api/v1/pedidos"]

    assert "/api/v1/pedidos/{pedido_id}" in paths
    assert "get" in paths["/api/v1/pedidos/{pedido_id}"]

    assert "/api/v1/pedidos/{pedido_id}/status" in paths
    assert "patch" in paths["/api/v1/pedidos/{pedido_id}/status"]


def test_openapi_health_endpoint_continua_sem_versao(client: TestClient) -> None:
    """O `/health` permanece no root, sem o prefixo `/api/v1`."""
    paths = client.get("/openapi.json").json()["paths"]
    assert "/health" in paths
    assert "/api/v1/health" not in paths


def test_docs_endpoint_responde_200(client: TestClient) -> None:
    """A UI Swagger (`/docs`) responde 200 e é HTML."""
    r = client.get("/docs")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
