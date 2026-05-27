"""Serviço de domínio para AtendimentoPedido."""

from app.core.errors import DoadorNotFoundError, PedidoNotAtendivelError, PedidoNotFoundError
from app.models.atendimento import AtendimentoPedido
from app.models.enums import StatusPedidoEnum
from app.repositories.atendimento_repository import AtendimentoRepository
from app.repositories.doador_repository import DoadorRepository
from app.repositories.pedido_repository import PedidoRepository
from app.schemas import AtendimentoCreate, PedidoStatusUpdate


class AtendimentoService:
    """Operações de negócio sobre AtendimentoPedido."""

    def __init__(
        self,
        atendimento_repository: AtendimentoRepository,
        pedido_repository: PedidoRepository,
        doador_repository: DoadorRepository,
    ) -> None:
        """Inicializa o serviço com os repositórios necessários.

        Args:
            atendimento_repository: Repositório usado para persistir atendimentos.
            pedido_repository: Repositório usado para consultar e atualizar pedidos.
            doador_repository: Repositório usado para validar doadores.
        """
        self.atendimento_repository = atendimento_repository
        self.pedido_repository = pedido_repository
        self.doador_repository = doador_repository

    def create(self, pedido_id: int, payload: AtendimentoCreate) -> AtendimentoPedido:
        """Cria um atendimento para um pedido atendível.

        Args:
            pedido_id: Identificador do pedido que receberá o atendimento.
            payload: Dados validados do atendimento, incluindo `doador_id`.

        Returns:
            Atendimento criado.

        Raises:
            PedidoNotFoundError: Se o pedido não existir.
            DoadorNotFoundError: Se o doador não existir.
            PedidoNotAtendivelError: Se o pedido estiver concluído.
        """
        pedido = self.pedido_repository.get_by_id(pedido_id)
        if pedido is None:
            raise PedidoNotFoundError(f"Pedido id={pedido_id} não existe.")

        if self.doador_repository.get_by_id(payload.doador_id) is None:
            raise DoadorNotFoundError(f"Doador id={payload.doador_id} não existe.")

        if pedido.status is StatusPedidoEnum.CONCLUIDO:
            raise PedidoNotAtendivelError(
                f"Pedido id={pedido_id} está concluído e não pode receber atendimento."
            )

        try:
            atendimento = self.atendimento_repository.create(pedido_id, payload, commit=False)
            if pedido.status is StatusPedidoEnum.ABERTO:
                atualizado = self.pedido_repository.update_status(
                    pedido_id,
                    PedidoStatusUpdate(status=StatusPedidoEnum.EM_ANDAMENTO),
                    commit=False,
                )
                if atualizado is None:
                    raise PedidoNotFoundError(f"Pedido id={pedido_id} não existe.")
            self.atendimento_repository.session.commit()
            self.atendimento_repository.session.refresh(atendimento)
        except Exception:
            self.atendimento_repository.session.rollback()
            raise
        return atendimento

    def list_by_pedido(self, pedido_id: int) -> list[AtendimentoPedido]:
        """Lista atendimentos de um pedido existente.

        Args:
            pedido_id: Identificador do pedido.

        Returns:
            Lista de atendimentos vinculados ao pedido.

        Raises:
            PedidoNotFoundError: Se o pedido não existir.
        """
        if self.pedido_repository.get_by_id(pedido_id) is None:
            raise PedidoNotFoundError(f"Pedido id={pedido_id} não existe.")
        return self.atendimento_repository.list_by_pedido(pedido_id)
