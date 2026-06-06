"""Abstração de armazenamento de arquivos enviados (upload de imagens).

Define a interface `StorageBackend` e duas implementações: uma local em disco
(`LocalStorageBackend`), usada em desenvolvimento e testes, e uma de object
storage S3-compatível (`S3StorageBackend`) para produção — serve Cloudflare R2,
AWS S3, Supabase Storage e MinIO. A escolha do backend é injetável via
`get_storage`, mantendo a camada de serviço/rotas desacoplada do meio de
persistência. O backend local segue como default de desenvolvimento.
"""

from __future__ import annotations

import logging
import mimetypes
from abc import ABC, abstractmethod
from pathlib import Path

from app.config import Settings

logger = logging.getLogger(__name__)

#: Content-type usado quando a extensão do arquivo não é reconhecida.
_FALLBACK_CONTENT_TYPE = "application/octet-stream"


class StorageBackend(ABC):
    """Interface de armazenamento de arquivos enviados.

    Implementações concretas persistem o conteúdo binário e devolvem uma URL
    pública estável para o arquivo. A URL é o identificador usado depois para
    remover o arquivo, mantendo a interface independente do meio de persistência.
    """

    @abstractmethod
    def salvar(self, conteudo: bytes, nome_arquivo: str) -> str:
        """Persiste o conteúdo binário sob o nome informado.

        Args:
            conteudo: bytes do arquivo a gravar.
            nome_arquivo: nome final do arquivo (já único, com extensão).

        Returns:
            URL pública relativa pela qual o arquivo será servido.

        Side Effects:
            Grava o arquivo no meio de persistência do backend.
        """

    @abstractmethod
    def remover(self, url: str) -> None:
        """Remove o arquivo identificado pela URL pública.

        A operação é idempotente: remover uma URL cujo arquivo já não existe
        não deve levantar erro.

        Args:
            url: URL pública retornada por `salvar`.

        Side Effects:
            Apaga o arquivo correspondente no meio de persistência.
        """


class LocalStorageBackend(StorageBackend):
    """Armazena arquivos no sistema de arquivos local.

    Grava os uploads em um diretório configurável e os serve sob um prefixo
    público (montado como `StaticFiles` no app). Adequado a desenvolvimento e
    testes; em produção seria substituído por um backend de object storage.

    Atributos:
        diretorio: caminho absoluto/relativo do diretório de uploads.
        public_path: prefixo público sob o qual os arquivos são expostos.
    """

    def __init__(self, diretorio: str, public_path: str) -> None:
        """Inicializa o backend local.

        Args:
            diretorio: diretório onde os arquivos serão gravados. Criado sob
                demanda no primeiro `salvar`.
            public_path: prefixo público dos arquivos (ex.: "/uploads"), sem
                barra final.
        """
        self._diretorio = Path(diretorio)
        self._public_path = public_path.rstrip("/")

    def salvar(self, conteudo: bytes, nome_arquivo: str) -> str:
        """Grava o conteúdo em `diretorio/nome_arquivo` e retorna a URL pública.

        Args:
            conteudo: bytes do arquivo.
            nome_arquivo: nome final (único, com extensão).

        Returns:
            URL pública relativa no formato `"{public_path}/{nome_arquivo}"`.

        Side Effects:
            Cria o diretório de uploads se ainda não existir e escreve o arquivo.
        """
        self._diretorio.mkdir(parents=True, exist_ok=True)
        destino = self._diretorio / nome_arquivo
        destino.write_bytes(conteudo)
        return f"{self._public_path}/{nome_arquivo}"

    def remover(self, url: str) -> None:
        """Apaga o arquivo apontado pela URL, se existir.

        Deriva o nome do arquivo a partir do sufixo da URL e remove o arquivo
        correspondente no diretório local. Idempotente.

        Args:
            url: URL pública retornada por `salvar`.

        Side Effects:
            Remove o arquivo do disco quando presente.
        """
        nome_arquivo = Path(url).name
        destino = self._diretorio / nome_arquivo
        destino.unlink(missing_ok=True)


def _content_type_de(nome_arquivo: str) -> str:
    """Deriva o content-type de um nome de arquivo a partir da extensão.

    Args:
        nome_arquivo: nome do arquivo (com extensão).

    Returns:
        Content-type adivinhado por `mimetypes.guess_type`, ou
        `"application/octet-stream"` quando a extensão não é reconhecida.
    """
    tipo, _ = mimetypes.guess_type(nome_arquivo)
    return tipo or _FALLBACK_CONTENT_TYPE


class S3StorageBackend(StorageBackend):
    """Armazena arquivos em object storage S3-compatível (R2/S3/Supabase/MinIO).

    Grava cada objeto sob a chave ``"{prefix}/{nome_arquivo}"`` no bucket
    configurado e devolve a URL pública ``"{public_base_url}/{prefix}/{nome}"``,
    servida por um domínio/CDN público (ex.: ``pub-xxx.r2.dev`` no Cloudflare R2
    ou um domínio próprio). A visibilidade pública vem do bucket/domínio público
    — nenhuma ACL é aplicada no `put_object`, pois o R2 não suporta ACLs.

    Atributos:
        bucket: nome do bucket de destino.
        public_base_url: base pública (sem barra final) das URLs retornadas.
        prefix: prefixo (pseudo-pasta) aplicado às chaves dos objetos.
    """

    def __init__(
        self,
        *,
        bucket: str,
        endpoint_url: str | None,
        region: str,
        access_key_id: str | None,
        secret_access_key: str | None,
        public_base_url: str,
        prefix: str,
    ) -> None:
        """Inicializa o backend e o client boto3 ``s3``.

        Args:
            bucket: nome do bucket onde os objetos são gravados.
            endpoint_url: endpoint do serviço S3-compatível (obrigatório para
                R2/MinIO/Supabase); `None` usa os endpoints padrão da AWS.
            region: região do bucket ("auto" no R2; região real na AWS).
            access_key_id: access key id (token S3).
            secret_access_key: secret access key (token S3).
            public_base_url: base pública/CDN das URLs (sem barra final
                obrigatória; é normalizada).
            prefix: prefixo das chaves dos objetos no bucket.

        Side Effects:
            Cria um client boto3 ``s3`` com o endpoint, região e credenciais
            informados.
        """
        import boto3

        self._bucket = bucket
        self._prefix = prefix.strip("/")
        self._public_base_url = public_base_url.rstrip("/")
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            region_name=region,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
        )

    def _key_de(self, nome_arquivo: str) -> str:
        """Monta a chave do objeto no bucket a partir do nome do arquivo.

        Args:
            nome_arquivo: nome final (único, com extensão).

        Returns:
            Chave no formato ``"{prefix}/{nome_arquivo}"``.
        """
        return f"{self._prefix}/{nome_arquivo}"

    def salvar(self, conteudo: bytes, nome_arquivo: str) -> str:
        """Grava o objeto no bucket e retorna sua URL pública.

        Args:
            conteudo: bytes do arquivo.
            nome_arquivo: nome final (único, com extensão).

        Returns:
            URL pública no formato ``"{public_base_url}/{prefix}/{nome}"``.

        Raises:
            RuntimeError: se o `put_object` falhar (erro do boto3), sem vazar
                credenciais na mensagem.

        Side Effects:
            Faz `put_object` no bucket configurado.
        """
        from botocore.exceptions import ClientError

        key = self._key_de(nome_arquivo)
        try:
            self._client.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=conteudo,
                ContentType=_content_type_de(nome_arquivo),
            )
        except ClientError as exc:
            codigo = exc.response.get("Error", {}).get("Code", "desconhecido")
            raise RuntimeError(
                f"Falha ao gravar o objeto '{key}' no bucket de storage (código {codigo})."
            ) from exc
        return f"{self._public_base_url}/{key}"

    def remover(self, url: str) -> None:
        """Remove o objeto identificado pela URL pública. Idempotente.

        Deriva a chave removendo o prefixo `public_base_url` da URL. Se a URL
        não casar a base pública, registra um aviso e não levanta (mantendo a
        operação tolerante a URLs antigas/externas). Erros do boto3 também são
        registrados sem interromper o fluxo de remoção.

        Args:
            url: URL pública retornada por `salvar`.

        Side Effects:
            Faz `delete_object` no bucket quando a chave é derivável.
        """
        from botocore.exceptions import ClientError

        prefixo_base = f"{self._public_base_url}/"
        if not url.startswith(prefixo_base):
            logger.warning("URL '%s' não casa a base pública do storage S3; remoção ignorada.", url)
            return
        key = url[len(prefixo_base) :]
        try:
            self._client.delete_object(Bucket=self._bucket, Key=key)
        except ClientError as exc:
            codigo = exc.response.get("Error", {}).get("Code", "desconhecido")
            logger.warning(
                "Falha ao remover o objeto '%s' do storage S3 (código %s); ignorando.",
                key,
                codigo,
            )


def _build_s3_storage(settings: Settings) -> S3StorageBackend:
    """Constrói um `S3StorageBackend` validando a configuração obrigatória.

    Args:
        settings: configurações da aplicação com os campos `s3_*`.

    Returns:
        Backend S3 pronto para uso.

    Raises:
        ValueError: se faltar algum campo obrigatório (`s3_bucket`,
            `s3_public_base_url` ou as credenciais), com mensagem que cita
            `storage_backend` e os campos ausentes — sem vazar valores.
    """
    faltando = [
        nome
        for nome, valor in (
            ("s3_bucket", settings.s3_bucket),
            ("s3_public_base_url", settings.s3_public_base_url),
            ("s3_access_key_id", settings.s3_access_key_id),
            ("s3_secret_access_key", settings.s3_secret_access_key),
        )
        if not valor
    ]
    if faltando:
        raise ValueError(
            "Configuração inválida para storage_backend='s3': defina " + ", ".join(faltando) + "."
        )
    return S3StorageBackend(
        bucket=settings.s3_bucket,
        endpoint_url=settings.s3_endpoint_url,
        region=settings.s3_region,
        access_key_id=settings.s3_access_key_id,
        secret_access_key=settings.s3_secret_access_key,
        public_base_url=settings.s3_public_base_url,
        prefix=settings.s3_prefix,
    )


def get_storage(settings: Settings) -> StorageBackend:
    """Factory do backend de storage a partir das Settings.

    Seleciona o backend conforme `settings.storage_backend`: "s3" devolve um
    `S3StorageBackend` (validando a configuração obrigatória) e qualquer outro
    valor — incluindo o default "local" — devolve um `LocalStorageBackend`.
    Este é o ponto único de decisão, mantendo rotas e serviços desacoplados do
    meio de persistência.

    Args:
        settings: configurações da aplicação (backend e parâmetros de storage).

    Returns:
        Instância de `StorageBackend` pronta para uso.

    Raises:
        ValueError: se `storage_backend == "s3"` e faltar configuração
            obrigatória do S3.
    """
    if settings.storage_backend == "s3":
        return _build_s3_storage(settings)
    return LocalStorageBackend(
        diretorio=settings.upload_dir,
        public_path=settings.public_upload_path,
    )
