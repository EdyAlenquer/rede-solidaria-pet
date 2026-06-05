"""Testes unitários da abstração de storage de arquivos."""

from pathlib import Path

import pytest

from app.config import Settings
from app.core.storage import LocalStorageBackend, StorageBackend, get_storage


def test_local_storage_salva_e_retorna_url_publica(tmp_path: Path) -> None:
    """`salvar` grava o arquivo no diretório e retorna a URL pública relativa."""
    backend = LocalStorageBackend(diretorio=str(tmp_path), public_path="/uploads")

    url = backend.salvar(b"conteudo-binario", "foto.jpg")

    assert url == "/uploads/foto.jpg"
    assert (tmp_path / "foto.jpg").read_bytes() == b"conteudo-binario"


def test_local_storage_cria_diretorio_se_nao_existir(tmp_path: Path) -> None:
    """O diretório de upload é criado automaticamente ao salvar."""
    destino = tmp_path / "subdir" / "uploads"
    backend = LocalStorageBackend(diretorio=str(destino), public_path="/uploads")

    backend.salvar(b"x", "a.png")

    assert (destino / "a.png").exists()


def test_local_storage_remove_arquivo_pela_url(tmp_path: Path) -> None:
    """`remover` apaga o arquivo correspondente à URL pública."""
    backend = LocalStorageBackend(diretorio=str(tmp_path), public_path="/uploads")
    url = backend.salvar(b"x", "remover.webp")
    assert (tmp_path / "remover.webp").exists()

    backend.remover(url)

    assert not (tmp_path / "remover.webp").exists()


def test_local_storage_remover_inexistente_nao_falha(tmp_path: Path) -> None:
    """Remover uma URL cujo arquivo não existe é idempotente (não levanta)."""
    backend = LocalStorageBackend(diretorio=str(tmp_path), public_path="/uploads")

    backend.remover("/uploads/inexistente.jpg")  # não deve levantar


def test_local_storage_e_um_storage_backend(tmp_path: Path) -> None:
    """`LocalStorageBackend` implementa a interface `StorageBackend`."""
    backend = LocalStorageBackend(diretorio=str(tmp_path), public_path="/uploads")
    assert isinstance(backend, StorageBackend)


def test_storage_backend_e_abstrato() -> None:
    """`StorageBackend` não pode ser instanciada diretamente (é abstrata)."""
    with pytest.raises(TypeError):
        StorageBackend()  # type: ignore[abstract]


def test_get_storage_usa_settings_para_local_backend(tmp_path: Path) -> None:
    """`get_storage` constrói um `LocalStorageBackend` a partir das Settings."""
    settings = Settings(upload_dir=str(tmp_path), public_upload_path="/midia")
    backend = get_storage(settings)

    url = backend.salvar(b"y", "z.jpg")
    assert url == "/midia/z.jpg"
    assert isinstance(backend, LocalStorageBackend)
