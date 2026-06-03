"""Testes de integração dos endpoints de imagens de pedido."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app

_VALID_PAYLOAD = {
    "titulo": "Cãozinho ferido",
    "descricao": "Encontrado na rua X, precisa de atendimento veterinário.",
    "categoria": "resgate",
    "urgencia": "alta",
    "contato": "11999990000",
    "cidade": "São Paulo",
    "estado": "SP",
    "consentimento_aceito": True,
}

#: PNG 1x1 mínimo válido (header + dados), suficiente para os testes de upload.
_PNG_1X1 = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000a49444154789c6360000002000154a24f9b0000000049454e44ae426082"
)


@pytest.fixture
def upload_dir(tmp_path: Path) -> Path:
    """Diretório temporário de uploads, isolado por teste.

    Args:
        tmp_path: diretório temporário do pytest.

    Returns:
        Caminho do diretório de uploads do teste.
    """
    return tmp_path / "uploads"


@pytest.fixture
def imagens_client(api_client: TestClient, upload_dir: Path) -> Iterator[TestClient]:
    """`api_client` com `get_settings` overridado para um upload_dir temporário.

    Mantém o override de `get_db` já aplicado por `api_client` e adiciona o
    override de `get_settings`, garantindo que os arquivos sejam gravados num
    diretório temporário (limpo automaticamente pelo `tmp_path`).

    Yields:
        Cliente HTTP de teste com storage isolado.
    """

    def _override_get_settings() -> Settings:
        return Settings(
            upload_dir=str(upload_dir),
            public_upload_path="/uploads",
            max_upload_bytes=1024,
            max_imagens_por_pedido=2,
            rate_limit_enabled=False,
        )

    app.dependency_overrides[get_settings] = _override_get_settings
    try:
        yield api_client
    finally:
        app.dependency_overrides.pop(get_settings, None)


def _criar_pedido(client: TestClient, headers: dict) -> int:
    """Cria um pedido e retorna seu id."""
    r = client.post("/api/v1/pedidos", json=_VALID_PAYLOAD, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_upload_valido_cria_imagem_e_grava_arquivo(
    imagens_client: TestClient, auth_headers: dict, upload_dir: Path
) -> None:
    """POST imagens com arquivo válido retorna 201, grava o arquivo e a linha."""
    pedido_id = _criar_pedido(imagens_client, auth_headers)

    r = imagens_client.post(
        f"/api/v1/pedidos/{pedido_id}/imagens",
        files={"arquivo": ("foto.png", _PNG_1X1, "image/png")},
        headers=auth_headers,
    )

    assert r.status_code == 201, r.text
    body = r.json()
    assert body["url"].startswith("/uploads/")
    assert body["url"].endswith(".png")
    assert body["ordem"] == 0
    nome = body["url"].rsplit("/", 1)[-1]
    assert (upload_dir / nome).read_bytes() == _PNG_1X1


def test_upload_aparece_em_get_pedido_e_em_get_imagens(
    imagens_client: TestClient, auth_headers: dict
) -> None:
    """A imagem enviada aparece em GET /pedidos/{id} e em GET de imagens."""
    pedido_id = _criar_pedido(imagens_client, auth_headers)
    imagens_client.post(
        f"/api/v1/pedidos/{pedido_id}/imagens",
        files={"arquivo": ("foto.png", _PNG_1X1, "image/png")},
        headers=auth_headers,
    )

    detalhe = imagens_client.get(f"/api/v1/pedidos/{pedido_id}")
    assert detalhe.status_code == 200
    assert len(detalhe.json()["imagens"]) == 1

    listagem = imagens_client.get(f"/api/v1/pedidos/{pedido_id}/imagens")
    assert listagem.status_code == 200
    assert len(listagem.json()) == 1
    assert listagem.json()[0]["ordem"] == 0


def test_upload_sem_auth_retorna_401(imagens_client: TestClient, auth_headers: dict) -> None:
    """POST imagens sem Bearer retorna 401."""
    pedido_id = _criar_pedido(imagens_client, auth_headers)

    r = imagens_client.post(
        f"/api/v1/pedidos/{pedido_id}/imagens",
        files={"arquivo": ("foto.png", _PNG_1X1, "image/png")},
    )
    assert r.status_code == 401


def test_upload_tipo_invalido_retorna_415(imagens_client: TestClient, auth_headers: dict) -> None:
    """Content-type não permitido retorna 415."""
    pedido_id = _criar_pedido(imagens_client, auth_headers)

    r = imagens_client.post(
        f"/api/v1/pedidos/{pedido_id}/imagens",
        files={"arquivo": ("doc.pdf", b"%PDF-1.4", "application/pdf")},
        headers=auth_headers,
    )
    assert r.status_code == 415
    assert r.headers["content-type"] == "application/problem+json"


def test_upload_tamanho_excedido_retorna_413(
    imagens_client: TestClient, auth_headers: dict
) -> None:
    """Arquivo maior que max_upload_bytes retorna 413."""
    pedido_id = _criar_pedido(imagens_client, auth_headers)
    grande = b"x" * 2048  # > 1024 (limite do override)

    r = imagens_client.post(
        f"/api/v1/pedidos/{pedido_id}/imagens",
        files={"arquivo": ("grande.png", grande, "image/png")},
        headers=auth_headers,
    )
    assert r.status_code == 413


def test_upload_limite_por_pedido_retorna_409(
    imagens_client: TestClient, auth_headers: dict
) -> None:
    """Exceder o limite de imagens por pedido retorna 409."""
    pedido_id = _criar_pedido(imagens_client, auth_headers)
    for _ in range(2):  # atinge o limite (2)
        r = imagens_client.post(
            f"/api/v1/pedidos/{pedido_id}/imagens",
            files={"arquivo": ("foto.png", _PNG_1X1, "image/png")},
            headers=auth_headers,
        )
        assert r.status_code == 201

    r = imagens_client.post(
        f"/api/v1/pedidos/{pedido_id}/imagens",
        files={"arquivo": ("foto.png", _PNG_1X1, "image/png")},
        headers=auth_headers,
    )
    assert r.status_code == 409


def test_upload_nao_autor_retorna_403(
    imagens_client: TestClient, auth_headers: dict, auth_headers_outro: dict
) -> None:
    """Usuário que não é autor do pedido recebe 403 ao subir imagem."""
    pedido_id = _criar_pedido(imagens_client, auth_headers)

    r = imagens_client.post(
        f"/api/v1/pedidos/{pedido_id}/imagens",
        files={"arquivo": ("foto.png", _PNG_1X1, "image/png")},
        headers=auth_headers_outro,
    )
    assert r.status_code == 403


def test_get_imagens_publico(imagens_client: TestClient, auth_headers: dict) -> None:
    """GET de imagens é público (sem auth) e retorna lista vazia inicialmente."""
    pedido_id = _criar_pedido(imagens_client, auth_headers)

    r = imagens_client.get(f"/api/v1/pedidos/{pedido_id}/imagens")
    assert r.status_code == 200
    assert r.json() == []


def test_delete_remove_imagem_e_arquivo(
    imagens_client: TestClient, auth_headers: dict, upload_dir: Path
) -> None:
    """DELETE remove a linha e o arquivo do storage e retorna 204."""
    pedido_id = _criar_pedido(imagens_client, auth_headers)
    criada = imagens_client.post(
        f"/api/v1/pedidos/{pedido_id}/imagens",
        files={"arquivo": ("foto.png", _PNG_1X1, "image/png")},
        headers=auth_headers,
    ).json()
    imagem_id = criada["id"]
    nome = criada["url"].rsplit("/", 1)[-1]
    assert (upload_dir / nome).exists()

    r = imagens_client.delete(
        f"/api/v1/pedidos/{pedido_id}/imagens/{imagem_id}", headers=auth_headers
    )
    assert r.status_code == 204
    assert not (upload_dir / nome).exists()

    listagem = imagens_client.get(f"/api/v1/pedidos/{pedido_id}/imagens")
    assert listagem.json() == []


def test_delete_inexistente_retorna_404(imagens_client: TestClient, auth_headers: dict) -> None:
    """DELETE de imagem inexistente retorna 404."""
    pedido_id = _criar_pedido(imagens_client, auth_headers)

    r = imagens_client.delete(f"/api/v1/pedidos/{pedido_id}/imagens/99999", headers=auth_headers)
    assert r.status_code == 404


def test_delete_nao_autor_retorna_403(
    imagens_client: TestClient, auth_headers: dict, auth_headers_outro: dict
) -> None:
    """DELETE por usuário que não é autor nem admin retorna 403."""
    pedido_id = _criar_pedido(imagens_client, auth_headers)
    imagem_id = imagens_client.post(
        f"/api/v1/pedidos/{pedido_id}/imagens",
        files={"arquivo": ("foto.png", _PNG_1X1, "image/png")},
        headers=auth_headers,
    ).json()["id"]

    r = imagens_client.delete(
        f"/api/v1/pedidos/{pedido_id}/imagens/{imagem_id}", headers=auth_headers_outro
    )
    assert r.status_code == 403
