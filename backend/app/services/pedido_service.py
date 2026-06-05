"""Serviço de domínio para PedidoAjuda."""

from app.core.errors import (
    AcessoNegadoError,
    InvalidStatusTransitionError,
    PedidoNotFoundError,
)
from app.models.enums import PapelUsuarioEnum, StatusPedidoEnum
from app.models.pedido import PedidoAjuda
from app.models.usuario import Usuario
from app.repositories.pedido_repository import PedidoRepository
from app.schemas import PedidoCreate, PedidoStatusUpdate, PedidoUpdate

# Máquina de estados explícita: mapa de adjacência das transições permitidas.
# Cada chave aponta para o conjunto de estados alcançáveis a partir dela.
# A transição para o mesmo estado é tratada à parte como no-op idempotente.
#
#   ABERTO        -> EM_ANDAMENTO, CANCELADO
#   EM_ANDAMENTO  -> CONCLUIDO, CANCELADO, ABERTO (reabrir)
#   CONCLUIDO     -> EM_ANDAMENTO (reabrir)
#   CANCELADO     -> ABERTO (reabrir)
_TRANSICOES_PERMITIDAS: dict[StatusPedidoEnum, frozenset[StatusPedidoEnum]] = {
    StatusPedidoEnum.ABERTO: frozenset({StatusPedidoEnum.EM_ANDAMENTO, StatusPedidoEnum.CANCELADO}),
    StatusPedidoEnum.EM_ANDAMENTO: frozenset(
        {StatusPedidoEnum.CONCLUIDO, StatusPedidoEnum.CANCELADO, StatusPedidoEnum.ABERTO}
    ),
    StatusPedidoEnum.CONCLUIDO: frozenset({StatusPedidoEnum.EM_ANDAMENTO}),
    StatusPedidoEnum.CANCELADO: frozenset({StatusPedidoEnum.ABERTO}),
}


def _is_valid_transition(atual: StatusPedidoEnum, novo: StatusPedidoEnum) -> bool:
    """Decide se a transição `atual -> novo` é permitida pela máquina de estados.

    A transição para o mesmo estado (`atual == novo`) é sempre considerada
    válida e tratada como no-op idempotente pela camada de serviço.

    Args:
        atual: status atual do pedido.
        novo: status pretendido.

    Returns:
        True se `novo` for igual a `atual` (idempotente) ou estiver no conjunto
        de destinos permitidos a partir de `atual`; False caso contrário.
    """
    if novo is atual:
        return True
    return novo in _TRANSICOES_PERMITIDAS[atual]


class PedidoService:
    """Operações de negócio sobre PedidoAjuda."""

    def __init__(self, repository: PedidoRepository) -> None:
        """Inicializa o serviço com um repositório de pedidos.

        Args:
            repository: repositório a ser usado.
        """
        self.repository = repository

    def create(self, payload: PedidoCreate, *, autor_id: int | None = None) -> PedidoAjuda:
        """Cria um pedido vinculado ao autor informado.

        Args:
            payload: dados do pedido.
            autor_id: id do usuário autor; definido pela camada de API a partir
                do usuário autenticado. `None` apenas para pedidos sem autor.

        Returns:
            Pedido criado.
        """
        return self.repository.create(payload, autor_id=autor_id)

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

    def get_public_by_id(self, pedido_id: int) -> PedidoAjuda:
        """Busca um pedido para leitura pública (ativo e não oculto).

        Args:
            pedido_id: identificador.

        Returns:
            Pedido encontrado, ativo e não oculto.

        Raises:
            PedidoNotFoundError: se o pedido não existir, estiver soft-deletado
                ou tiver sido ocultado pela moderação.
        """
        pedido = self.repository.get_public_by_id(pedido_id)
        if pedido is None:
            raise PedidoNotFoundError(f"Pedido id={pedido_id} não existe.")
        return pedido

    def _autorizar_autor_ou_admin(self, pedido: PedidoAjuda, usuario: Usuario) -> None:
        """Garante que o usuário é o autor do pedido ou um administrador.

        Args:
            pedido: pedido alvo da operação.
            usuario: usuário autenticado solicitando a operação.

        Raises:
            AcessoNegadoError: se o usuário não for o autor nem administrador.
        """
        if usuario.papel is PapelUsuarioEnum.ADMIN:
            return
        if pedido.autor_id == usuario.id:
            return
        raise AcessoNegadoError("Apenas o autor ou um administrador pode alterar este pedido.")

    def update(self, pedido_id: int, payload: PedidoUpdate, *, usuario: Usuario) -> PedidoAjuda:
        """Atualiza parcialmente um pedido, restrito ao autor ou admin.

        Args:
            pedido_id: identificador do pedido.
            payload: campos a atualizar.
            usuario: usuário autenticado (deve ser autor ou admin).

        Returns:
            Pedido atualizado.

        Raises:
            PedidoNotFoundError: se o pedido não existir (ou estiver soft-deletado).
            AcessoNegadoError: se o usuário não for autor nem admin.
        """
        pedido = self.get_by_id(pedido_id)
        self._autorizar_autor_ou_admin(pedido, usuario)
        atualizado = self.repository.update(pedido_id, payload)
        if atualizado is None:
            raise PedidoNotFoundError(f"Pedido id={pedido_id} não existe.")
        return atualizado

    def delete(self, pedido_id: int, *, usuario: Usuario) -> None:
        """Remove (soft-delete) um pedido, restrito ao autor ou admin.

        Args:
            pedido_id: identificador do pedido.
            usuario: usuário autenticado (deve ser autor ou admin).

        Raises:
            PedidoNotFoundError: se o pedido não existir (ou já estiver soft-deletado).
            AcessoNegadoError: se o usuário não for autor nem admin.
        """
        pedido = self.get_by_id(pedido_id)
        self._autorizar_autor_ou_admin(pedido, usuario)
        if not self.repository.soft_delete(pedido_id):
            raise PedidoNotFoundError(f"Pedido id={pedido_id} não existe.")

    def change_status(
        self, pedido_id: int, payload: PedidoStatusUpdate, *, usuario: Usuario
    ) -> PedidoAjuda:
        """Aplica uma mudança de status validando autoria e a transição.

        Args:
            pedido_id: identificador do pedido.
            payload: novo status pretendido.
            usuario: usuário autenticado (deve ser autor ou admin).

        Returns:
            Pedido atualizado (ou inalterado, se transição idempotente).

        Raises:
            PedidoNotFoundError: se o pedido não existir.
            AcessoNegadoError: se o usuário não for autor nem admin.
            InvalidStatusTransitionError: se a transição não for permitida.
        """
        pedido = self.get_by_id(pedido_id)
        self._autorizar_autor_ou_admin(pedido, usuario)
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
