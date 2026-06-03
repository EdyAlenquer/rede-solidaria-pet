"""Serviço de domínio para moderação: denúncias e ocultação de pedidos."""

from app.core.errors import DenunciaNotFoundError, PedidoNotFoundError
from app.models.denuncia import Denuncia
from app.models.pedido import PedidoAjuda
from app.repositories.denuncia_repository import DenunciaRepository
from app.repositories.pedido_repository import PedidoRepository
from app.schemas import DenunciaCreate


class DenunciaService:
    """Operações de negócio de moderação (denúncias e visibilidade de pedidos)."""

    def __init__(
        self,
        denuncia_repository: DenunciaRepository,
        pedido_repository: PedidoRepository,
    ) -> None:
        """Inicializa o serviço com os repositórios necessários.

        Args:
            denuncia_repository: repositório de denúncias.
            pedido_repository: repositório de pedidos (para validar e ocultar).
        """
        self.denuncia_repository = denuncia_repository
        self.pedido_repository = pedido_repository

    def criar(self, pedido_id: int, payload: DenunciaCreate, *, autor_id: int) -> Denuncia:
        """Registra uma denúncia para um pedido existente.

        Args:
            pedido_id: id do pedido denunciado.
            payload: dados da denúncia (`motivo`, `descricao`).
            autor_id: id do usuário denunciante.

        Returns:
            Denúncia criada.

        Raises:
            PedidoNotFoundError: se o pedido não existir (ou estiver soft-deletado).
        """
        if self.pedido_repository.get_by_id(pedido_id) is None:
            raise PedidoNotFoundError(f"Pedido id={pedido_id} não existe.")
        return self.denuncia_repository.create(pedido_id, payload, autor_id=autor_id)

    def listar(self) -> list[Denuncia]:
        """Lista todas as denúncias para a moderação.

        Returns:
            Lista de denúncias, das mais recentes para as mais antigas.
        """
        return self.denuncia_repository.list()

    def resolver(self, denuncia_id: int) -> Denuncia:
        """Marca uma denúncia como resolvida.

        Args:
            denuncia_id: id da denúncia.

        Returns:
            Denúncia atualizada.

        Raises:
            DenunciaNotFoundError: se a denúncia não existir.
        """
        denuncia = self.denuncia_repository.resolver(denuncia_id)
        if denuncia is None:
            raise DenunciaNotFoundError(f"Denúncia id={denuncia_id} não existe.")
        return denuncia

    def definir_visibilidade(self, pedido_id: int, *, oculto: bool) -> PedidoAjuda:
        """Oculta ou reexibe um pedido (ação de moderação).

        Args:
            pedido_id: id do pedido alvo.
            oculto: True para ocultar, False para reexibir.

        Returns:
            Pedido atualizado.

        Raises:
            PedidoNotFoundError: se o pedido não existir (ou estiver soft-deletado).
        """
        pedido = self.pedido_repository.set_oculto(pedido_id, oculto)
        if pedido is None:
            raise PedidoNotFoundError(f"Pedido id={pedido_id} não existe.")
        return pedido
