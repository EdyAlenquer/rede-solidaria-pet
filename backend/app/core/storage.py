"""Abstração de armazenamento de arquivos enviados (upload de imagens).

Define a interface `StorageBackend` e uma implementação local em disco
(`LocalStorageBackend`) usada em desenvolvimento e testes. A escolha do backend
é injetável via `get_storage`, deixando a costura pronta para, em produção,
trocar o backend local por um de object storage (Cloudinary, Cloudflare R2 ou
S3) sem alterar a camada de serviço/rotas. O backend de nuvem não é
implementado aqui por ainda não haver credenciais e por não ser testável neste
estágio; a interface foi mantida mínima e estável para acomodá-lo depois.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from app.config import Settings


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


def get_storage(settings: Settings) -> StorageBackend:
    """Factory do backend de storage a partir das Settings.

    Hoje devolve sempre o `LocalStorageBackend`. Este é o ponto único de
    decisão para, em produção, selecionar um backend de object storage
    (Cloudinary/R2/S3) conforme `settings` — mantendo rotas e serviços
    desacoplados do meio de persistência.

    Args:
        settings: configurações da aplicação (diretório e prefixo público).

    Returns:
        Instância de `StorageBackend` pronta para uso.
    """
    return LocalStorageBackend(
        diretorio=settings.upload_dir,
        public_path=settings.public_upload_path,
    )
