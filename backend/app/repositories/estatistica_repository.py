"""Repositório de estatísticas agregadas para o dashboard público."""

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.atendimento import AtendimentoPedido
from app.models.enums import StatusPedidoEnum
from app.models.pedido import PedidoAjuda


@dataclass(frozen=True)
class EstatisticasResultado:
    """Contadores agregados expostos pelo endpoint público de estatísticas.

    Attributes:
        total_pedidos: total de pedidos visíveis (não removidos nem ocultos).
        pedidos_abertos: pedidos visíveis com status ``aberto``.
        pedidos_concluidos: pedidos visíveis com status ``concluido``.
        total_atendimentos: total de atendimentos de pedidos visíveis.
        total_cidades: quantidade de cidades distintas entre os pedidos visíveis.
    """

    total_pedidos: int
    pedidos_abertos: int
    pedidos_concluidos: int
    total_atendimentos: int
    total_cidades: int


class EstatisticaRepository:
    """Consultas agregadas sobre pedidos e atendimentos visíveis.

    "Visível" significa não soft-deletado (`deleted_at IS NULL`) e não ocultado
    pela moderação (`oculto IS False`).
    """

    def __init__(self, session: Session) -> None:
        """Inicializa o repositório com uma sessão SQLAlchemy.

        Args:
            session: sessão ativa de banco.
        """
        self.session = session

    def coletar(self) -> EstatisticasResultado:
        """Coleta todos os contadores agregados em uma única passagem de consultas.

        Returns:
            `EstatisticasResultado` com os contadores do dashboard público.
        """
        visivel = (PedidoAjuda.deleted_at.is_(None), PedidoAjuda.oculto.is_(False))

        total_pedidos = int(
            self.session.scalar(select(func.count(PedidoAjuda.id)).where(*visivel)) or 0
        )
        pedidos_abertos = int(
            self.session.scalar(
                select(func.count(PedidoAjuda.id)).where(
                    *visivel, PedidoAjuda.status == StatusPedidoEnum.ABERTO
                )
            )
            or 0
        )
        pedidos_concluidos = int(
            self.session.scalar(
                select(func.count(PedidoAjuda.id)).where(
                    *visivel, PedidoAjuda.status == StatusPedidoEnum.CONCLUIDO
                )
            )
            or 0
        )
        total_cidades = int(
            self.session.scalar(
                select(func.count(func.distinct(PedidoAjuda.cidade))).where(*visivel)
            )
            or 0
        )
        total_atendimentos = int(
            self.session.scalar(
                select(func.count(AtendimentoPedido.id))
                .join(PedidoAjuda, AtendimentoPedido.pedido_id == PedidoAjuda.id)
                .where(*visivel)
            )
            or 0
        )

        return EstatisticasResultado(
            total_pedidos=total_pedidos,
            pedidos_abertos=pedidos_abertos,
            pedidos_concluidos=pedidos_concluidos,
            total_atendimentos=total_atendimentos,
            total_cidades=total_cidades,
        )
