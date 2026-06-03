"""Serviço de domínio para ImagemPedido (upload/listagem/remoção)."""

from uuid import uuid4

from app.config import Settings
from app.core.errors import (
    AcessoNegadoError,
    ImagemMuitoGrandeError,
    ImagemNotFoundError,
    LimiteImagensExcedidoError,
    PedidoNotFoundError,
    TipoImagemInvalidoError,
)
from app.core.storage import StorageBackend
from app.models.enums import PapelUsuarioEnum
from app.models.imagem import ImagemPedido
from app.models.pedido import PedidoAjuda
from app.models.usuario import Usuario
from app.repositories.imagem_repository import ImagemRepository
from app.repositories.pedido_repository import PedidoRepository

#: Extensão de arquivo associada a cada content-type de imagem aceito.
_EXTENSAO_POR_TIPO: dict[str, str] = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


class ImagemService:
    """Operações de negócio sobre imagens de um pedido.

    Orquestra validação (tipo, tamanho, limite por pedido), autorização (autor
    ou admin), gravação no `StorageBackend` e persistência da linha
    `ImagemPedido`, mantendo storage e banco consistentes.
    """

    def __init__(
        self,
        imagem_repository: ImagemRepository,
        pedido_repository: PedidoRepository,
        *,
        storage: StorageBackend,
        settings: Settings,
    ) -> None:
        """Inicializa o serviço com repositórios, storage e configurações.

        Args:
            imagem_repository: repositório de imagens.
            pedido_repository: repositório de pedidos (existência/autoria).
            storage: backend de armazenamento dos arquivos.
            settings: configurações de upload (limites e tipos permitidos).
        """
        self.imagem_repository = imagem_repository
        self.pedido_repository = pedido_repository
        self.storage = storage
        self.settings = settings

    def _obter_pedido(self, pedido_id: int) -> PedidoAjuda:
        """Carrega um pedido ativo ou levanta erro.

        Args:
            pedido_id: identificador do pedido.

        Returns:
            Pedido ativo.

        Raises:
            PedidoNotFoundError: se o pedido não existir (ou estiver removido).
        """
        pedido = self.pedido_repository.get_by_id(pedido_id)
        if pedido is None:
            raise PedidoNotFoundError(f"Pedido id={pedido_id} não existe.")
        return pedido

    def _autorizar_autor_ou_admin(self, pedido: PedidoAjuda, usuario: Usuario) -> None:
        """Garante que o usuário é o autor do pedido ou um administrador.

        Args:
            pedido: pedido alvo da operação.
            usuario: usuário autenticado solicitando a operação.

        Raises:
            AcessoNegadoError: se o usuário não for autor nem administrador.
        """
        if usuario.papel is PapelUsuarioEnum.ADMIN:
            return
        if pedido.autor_id == usuario.id:
            return
        raise AcessoNegadoError(
            "Apenas o autor ou um administrador pode gerenciar as imagens deste pedido."
        )

    def _validar_arquivo(self, conteudo: bytes, content_type: str) -> str:
        """Valida tipo e tamanho do arquivo enviado.

        Args:
            conteudo: bytes do arquivo.
            content_type: content-type declarado no upload.

        Returns:
            Extensão de arquivo derivada do content-type (ex.: "jpg").

        Raises:
            TipoImagemInvalidoError: se o content-type não for permitido.
            ImagemMuitoGrandeError: se o conteúdo exceder `max_upload_bytes`.
        """
        if content_type not in self.settings.allowed_image_types:
            permitidos = ", ".join(sorted(self.settings.allowed_image_types))
            raise TipoImagemInvalidoError(
                f"Tipo '{content_type}' não suportado. Permitidos: {permitidos}."
            )
        if len(conteudo) > self.settings.max_upload_bytes:
            limite_mb = self.settings.max_upload_bytes / (1024 * 1024)
            raise ImagemMuitoGrandeError(f"Imagem excede o tamanho máximo de {limite_mb:.0f} MB.")
        return _EXTENSAO_POR_TIPO[content_type]

    def create(
        self, pedido_id: int, conteudo: bytes, content_type: str, *, usuario: Usuario
    ) -> ImagemPedido:
        """Valida, grava no storage e persiste uma nova imagem do pedido.

        Args:
            pedido_id: identificador do pedido que receberá a imagem.
            conteudo: bytes do arquivo enviado.
            content_type: content-type declarado pelo cliente.
            usuario: usuário autenticado (deve ser autor ou admin).

        Returns:
            Imagem persistida (`ImagemPedido`) com `url` e `ordem`.

        Raises:
            PedidoNotFoundError: se o pedido não existir.
            AcessoNegadoError: se o usuário não for autor nem admin.
            TipoImagemInvalidoError: se o content-type não for permitido (415).
            ImagemMuitoGrandeError: se o tamanho exceder o limite (413).
            LimiteImagensExcedidoError: se o pedido já tiver o máximo de imagens.

        Side Effects:
            Grava o arquivo no storage e insere uma linha em `imagens_pedido`.
        """
        pedido = self._obter_pedido(pedido_id)
        self._autorizar_autor_ou_admin(pedido, usuario)
        extensao = self._validar_arquivo(conteudo, content_type)

        if (
            self.imagem_repository.count_by_pedido(pedido_id)
            >= self.settings.max_imagens_por_pedido
        ):
            raise LimiteImagensExcedidoError(
                f"Pedido id={pedido_id} já atingiu o máximo de "
                f"{self.settings.max_imagens_por_pedido} imagens."
            )

        nome_arquivo = f"{uuid4().hex}.{extensao}"
        url = self.storage.salvar(conteudo, nome_arquivo)
        try:
            return self.imagem_repository.create(pedido_id, url=url)
        except Exception:
            # Mantém storage e banco consistentes: desfaz o arquivo se a
            # persistência da linha falhar.
            self.storage.remover(url)
            raise

    def list_by_pedido(self, pedido_id: int) -> list[ImagemPedido]:
        """Lista as imagens de um pedido existente (acesso público).

        Args:
            pedido_id: identificador do pedido.

        Returns:
            Lista de imagens ordenada por `ordem`.

        Raises:
            PedidoNotFoundError: se o pedido não existir.
        """
        self._obter_pedido(pedido_id)
        return self.imagem_repository.list_by_pedido(pedido_id)

    def delete(self, pedido_id: int, imagem_id: int, *, usuario: Usuario) -> None:
        """Remove uma imagem do pedido (storage e banco), restrito a autor/admin.

        Args:
            pedido_id: identificador do pedido dono da imagem.
            imagem_id: identificador da imagem a remover.
            usuario: usuário autenticado (deve ser autor ou admin).

        Raises:
            PedidoNotFoundError: se o pedido não existir.
            AcessoNegadoError: se o usuário não for autor nem admin.
            ImagemNotFoundError: se a imagem não existir no pedido.

        Side Effects:
            Apaga o arquivo do storage e remove a linha de `imagens_pedido`.
        """
        pedido = self._obter_pedido(pedido_id)
        self._autorizar_autor_ou_admin(pedido, usuario)
        imagem = self.imagem_repository.get_by_id(pedido_id, imagem_id)
        if imagem is None:
            raise ImagemNotFoundError(f"Imagem id={imagem_id} não existe no pedido id={pedido_id}.")
        url = imagem.url
        self.imagem_repository.delete(imagem)
        self.storage.remover(url)
