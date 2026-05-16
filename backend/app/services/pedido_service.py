"""Serviço de domínio para PedidoAjuda."""

from app.core.errors import InvalidStatusTransitionError, PedidoNotFoundError
from app.models.enums import StatusPedidoEnum
from app.models.pedido import PedidoAjuda
from app.repositories.pedido_repository import PedidoRepository
from app.schemas import PedidoCreate, PedidoStatusUpdate

# Ordem canônica dos estados — uma transição só é válida se vai para frente
# (ou for idempotente). `concluido` é terminal.
_STATUS_ORDER: dict[StatusPedidoEnum, int] = {
    StatusPedidoEnum.ABERTO: 0,
    StatusPedidoEnum.EM_ANDAMENTO: 1,
    StatusPedidoEnum.CONCLUIDO: 2,
}


def _is_valid_transition(atual: StatusPedidoEnum, novo: StatusPedidoEnum) -> bool:
    """Decide se a transição `atual -> novo` é permitida.

    Args:
        atual: status atual do pedido.
        novo: status pretendido.

    Returns:
        True se `novo` for >= `atual` na ordem canônica.
    """
    return _STATUS_ORDER[novo] >= _STATUS_ORDER[atual]


class PedidoService:
    """Operações de negócio sobre PedidoAjuda."""

    def __init__(self, repository: PedidoRepository) -> None:
        """Inicializa o serviço com um repositório de pedidos.

        Args:
            repository: repositório a ser usado.
        """
        self.repository = repository

    def create(self, payload: PedidoCreate) -> PedidoAjuda:
        """Cria um pedido.

        Args:
            payload: dados do pedido.

        Returns:
            Pedido criado.
        """
        return self.repository.create(payload)

    def get_by_id(self, pedido_id: int) -> PedidoAjuda:
        """Busca um pedido pelo id.

        Args:
            pedido_id: identificador.

        Returns:
            Pedido encontrado.

        Raises:
            PedidoNotFoundError: se o pedido não existir.
        """
        pedido = self.repository.get_by_id(pedido_id)
        if pedido is None:
            raise PedidoNotFoundError(f"Pedido id={pedido_id} não existe.")
        return pedido

    def change_status(self, pedido_id: int, payload: PedidoStatusUpdate) -> PedidoAjuda:
        """Aplica uma mudança de status validando a transição.

        Args:
            pedido_id: identificador do pedido.
            payload: novo status pretendido.

        Returns:
            Pedido atualizado (ou inalterado, se transição idempotente).

        Raises:
            PedidoNotFoundError: se o pedido não existir.
            InvalidStatusTransitionError: se a transição não for permitida.
        """
        pedido = self.get_by_id(pedido_id)
        if not _is_valid_transition(pedido.status, payload.status):
            raise InvalidStatusTransitionError(
                f"Transição '{pedido.status.value}' -> '{payload.status.value}' não permitida."
            )
        if payload.status is pedido.status:
            return pedido  # no-op idempotente
        atualizado = self.repository.update_status(pedido_id, payload)
        # Race condition pós-get_by_id; trate como not-found.
        if atualizado is None:
            raise PedidoNotFoundError(f"Pedido id={pedido_id} não existe.")
        return atualizado
