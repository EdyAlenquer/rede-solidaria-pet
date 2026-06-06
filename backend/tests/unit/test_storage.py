"""Testes unitários da abstração de storage de arquivos."""

from pathlib import Path

import boto3
import pytest
from moto import mock_aws

from app.config import Settings
from app.core.storage import (
    LocalStorageBackend,
    S3StorageBackend,
    StorageBackend,
    get_storage,
)


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


# --- S3StorageBackend (object storage S3-compatível, mockado com moto) ---

_S3_BUCKET = "rede-solidaria-pet-test"
_S3_BASE_URL = "https://pub-abc123.r2.dev"
_S3_PREFIX = "pedidos"


def _criar_bucket(nome: str = _S3_BUCKET) -> "boto3.client":
    """Cria um bucket no S3 mockado e devolve o client boto3 usado.

    Args:
        nome: nome do bucket a criar.

    Returns:
        Client boto3 ("s3") apontando para o mock, com o bucket já criado.

    Side Effects:
        Cria o bucket informado no S3 mockado pelo moto.
    """
    client = boto3.client("s3", region_name="us-east-1")
    client.create_bucket(Bucket=nome)
    return client


def _build_s3_backend() -> S3StorageBackend:
    """Instancia um `S3StorageBackend` com a configuração de teste.

    Returns:
        Backend S3 apontando para o bucket/prefixo/base públicos de teste.
    """
    return S3StorageBackend(
        bucket=_S3_BUCKET,
        endpoint_url=None,
        region="us-east-1",
        access_key_id="testing",
        secret_access_key="testing",
        public_base_url=_S3_BASE_URL,
        prefix=_S3_PREFIX,
    )


@mock_aws
def test_s3_storage_e_um_storage_backend() -> None:
    """`S3StorageBackend` implementa a interface `StorageBackend`."""
    _criar_bucket()
    assert isinstance(_build_s3_backend(), StorageBackend)


@mock_aws
def test_s3_salvar_grava_objeto_e_retorna_url_publica() -> None:
    """`salvar` grava o objeto sob `prefix/nome` e retorna a URL pública."""
    client = _criar_bucket()
    backend = _build_s3_backend()

    url = backend.salvar(b"conteudo-jpg", "foto.jpg")

    assert url == f"{_S3_BASE_URL}/{_S3_PREFIX}/foto.jpg"
    obj = client.get_object(Bucket=_S3_BUCKET, Key=f"{_S3_PREFIX}/foto.jpg")
    assert obj["Body"].read() == b"conteudo-jpg"


@mock_aws
@pytest.mark.parametrize(
    ("nome", "content_type_esperado"),
    [
        ("foto.jpg", "image/jpeg"),
        ("foto.png", "image/png"),
        ("foto.webp", "image/webp"),
    ],
)
def test_s3_salvar_define_content_type_pela_extensao(nome: str, content_type_esperado: str) -> None:
    """O ContentType do objeto é derivado da extensão do nome do arquivo."""
    client = _criar_bucket()
    backend = _build_s3_backend()

    backend.salvar(b"x", nome)

    obj = client.get_object(Bucket=_S3_BUCKET, Key=f"{_S3_PREFIX}/{nome}")
    assert obj["ContentType"] == content_type_esperado


@mock_aws
def test_s3_salvar_extensao_desconhecida_usa_octet_stream() -> None:
    """Extensão sem mapeamento conhecido cai no fallback application/octet-stream."""
    client = _criar_bucket()
    backend = _build_s3_backend()

    backend.salvar(b"x", "arquivo.desconhecido")

    obj = client.get_object(Bucket=_S3_BUCKET, Key=f"{_S3_PREFIX}/arquivo.desconhecido")
    assert obj["ContentType"] == "application/octet-stream"


@mock_aws
def test_s3_remover_deleta_objeto() -> None:
    """`remover` apaga o objeto identificado pela URL pública."""
    client = _criar_bucket()
    backend = _build_s3_backend()
    url = backend.salvar(b"x", "remover.webp")
    assert client.get_object(Bucket=_S3_BUCKET, Key=f"{_S3_PREFIX}/remover.webp")

    backend.remover(url)

    with pytest.raises(client.exceptions.NoSuchKey):
        client.get_object(Bucket=_S3_BUCKET, Key=f"{_S3_PREFIX}/remover.webp")


@mock_aws
def test_s3_remover_objeto_inexistente_nao_falha() -> None:
    """Remover uma URL cujo objeto já não existe é idempotente (não levanta)."""
    _criar_bucket()
    backend = _build_s3_backend()

    backend.remover(f"{_S3_BASE_URL}/{_S3_PREFIX}/inexistente.jpg")  # não levanta


@mock_aws
def test_s3_remover_url_que_nao_casa_a_base_nao_levanta() -> None:
    """Remover uma URL que não começa pela base pública não levanta erro."""
    _criar_bucket()
    backend = _build_s3_backend()

    backend.remover("https://outro-dominio.example/pedidos/foto.jpg")  # não levanta


@mock_aws
def test_s3_salvar_erro_do_boto3_vira_runtimeerror_sem_vazar_credenciais() -> None:
    """`put_object` que falha (ClientError) vira RuntimeError sem expor credenciais.

    Exercita o ramo de tratamento de erro de `salvar`: aponta o backend para um
    bucket inexistente (sem `create_bucket`), forçando um `ClientError`
    (NoSuchBucket) no `put_object`. A exceção deve virar `RuntimeError` com o
    código do erro e sem conter a access key/secret na mensagem.
    """
    backend = S3StorageBackend(
        bucket="bucket-inexistente-xyz",
        endpoint_url=None,
        region="us-east-1",
        access_key_id="segredo-access-key",
        secret_access_key="segredo-secret-key",
        public_base_url=_S3_BASE_URL,
        prefix=_S3_PREFIX,
    )

    with pytest.raises(RuntimeError) as exc_info:
        backend.salvar(b"x", "foto.png")

    mensagem = str(exc_info.value)
    assert "NoSuchBucket" in mensagem
    assert "segredo-access-key" not in mensagem
    assert "segredo-secret-key" not in mensagem


@mock_aws
def test_s3_remover_erro_do_boto3_e_idempotente(caplog: pytest.LogCaptureFixture) -> None:
    """`delete_object` que falha (ClientError) é logado e não levanta.

    Exercita o ramo de tratamento de erro de `remover`: aponta o backend para um
    bucket inexistente, forçando `ClientError` (NoSuchBucket) no `delete_object`.
    A remoção deve registrar um aviso e retornar normalmente (idempotente), sem
    propagar a exceção do boto3.
    """
    import logging

    backend = S3StorageBackend(
        bucket="bucket-inexistente-xyz",
        endpoint_url=None,
        region="us-east-1",
        access_key_id="testing",
        secret_access_key="testing",
        public_base_url=_S3_BASE_URL,
        prefix=_S3_PREFIX,
    )

    with caplog.at_level(logging.WARNING, logger="app.core.storage"):
        backend.remover(f"{_S3_BASE_URL}/{_S3_PREFIX}/foto.png")  # não levanta

    assert any("NoSuchBucket" in rec.message for rec in caplog.records)


@mock_aws
def test_get_storage_s3_com_config_valida_retorna_s3_backend() -> None:
    """`get_storage` com `storage_backend="s3"` e config completa devolve S3."""
    _criar_bucket()
    settings = Settings(
        storage_backend="s3",
        s3_bucket=_S3_BUCKET,
        s3_region="us-east-1",
        s3_access_key_id="testing",
        s3_secret_access_key="testing",
        s3_public_base_url=_S3_BASE_URL,
        s3_prefix=_S3_PREFIX,
    )

    backend = get_storage(settings)

    assert isinstance(backend, S3StorageBackend)


@pytest.mark.parametrize("faltando", ["s3_bucket", "s3_public_base_url"])
def test_get_storage_s3_sem_config_obrigatoria_levanta(faltando: str) -> None:
    """`get_storage("s3")` sem bucket ou base pública levanta erro de config claro."""
    kwargs = dict(
        storage_backend="s3",
        s3_bucket=_S3_BUCKET,
        s3_access_key_id="testing",
        s3_secret_access_key="testing",
        s3_public_base_url=_S3_BASE_URL,
    )
    kwargs[faltando] = None
    settings = Settings(**kwargs)

    with pytest.raises(ValueError, match="storage_backend"):
        get_storage(settings)


def test_get_storage_s3_sem_credenciais_levanta() -> None:
    """`get_storage("s3")` sem credenciais levanta erro de configuração."""
    settings = Settings(
        storage_backend="s3",
        s3_bucket=_S3_BUCKET,
        s3_public_base_url=_S3_BASE_URL,
        s3_access_key_id=None,
        s3_secret_access_key=None,
    )

    with pytest.raises(ValueError, match="storage_backend"):
        get_storage(settings)
