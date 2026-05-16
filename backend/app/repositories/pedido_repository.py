"""Repositório de PedidoAjuda."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import StatusPedidoEnum, UrgenciaEnum
from app.models.pedido import PedidoAjuda
from app.schemas import PedidoCreate, PedidoStatusUpdate, PedidoUpdate


class PedidoRepository:
    """Operações de persistência para `PedidoAjuda`."""

    def __init__(self, session: Session) -> None:
        """Inicializa o repositório com uma sessão SQLAlchemy.

        Args:
            session: sessão ativa de banco.
        """
        self.session = session

    def create(self, payload: PedidoCreate) -> PedidoAjuda:
        """Cria e persiste um pedido a partir do payload.

        Args:
            payload: dados validados do pedido.

        Returns:
            Pedido recém-criado com `id` e `data_criacao` preenchidos.
        """
        pedido = PedidoAjuda(**payload.model_dump())
        self.session.add(pedido)
        self.session.commit()
        self.session.refresh(pedido)
        return pedido

    def get_by_id(self, pedido_id: int) -> PedidoAjuda | None:
        """Busca um pedido pelo id.

        Args:
            pedido_id: identificador.

        Returns:
            Pedido encontrado ou None.
        """
        return self.session.get(PedidoAjuda, pedido_id)

    def list(
        self,
        *,
        status: StatusPedidoEnum | None = None,
        urgencia: UrgenciaEnum | None = None,
        categoria: str | None = None,
    ) -> list[PedidoAjuda]:
        """Lista pedidos do mais recente para o mais antigo, com filtros opcionais.

        Args:
            status: se fornecido, filtra por status.
            urgencia: se fornecido, filtra por urgência.
            categoria: se fornecido, filtra por categoria (igualdade exata).

        Returns:
            Lista de pedidos ordenada por `data_criacao` desc.
        """
        stmt = select(PedidoAjuda).order_by(PedidoAjuda.data_criacao.desc(), PedidoAjuda.id.desc())
        if status is not None:
            stmt = stmt.where(PedidoAjuda.status == status)
        if urgencia is not None:
            stmt = stmt.where(PedidoAjuda.urgencia == urgencia)
        if categoria is not None:
            stmt = stmt.where(PedidoAjuda.categoria == categoria)
        return list(self.session.scalars(stmt).all())

    def update(self, pedido_id: int, payload: PedidoUpdate) -> PedidoAjuda | None:
        """Aplica atualização parcial em um pedido.

        Args:
            pedido_id: identificador do pedido alvo.
            payload: campos a atualizar (apenas os definidos são aplicados).

        Returns:
            Pedido atualizado ou None se não existir.
        """
        pedido = self.session.get(PedidoAjuda, pedido_id)
        if pedido is None:
            return None
        for campo, valor in payload.model_dump(exclude_unset=True).items():
            setattr(pedido, campo, valor)
        self.session.commit()
        self.session.refresh(pedido)
        return pedido

    def update_status(self, pedido_id: int, payload: PedidoStatusUpdate) -> PedidoAjuda | None:
        """Atualiza somente o status de um pedido.

        Args:
            pedido_id: identificador.
            payload: novo status.

        Returns:
            Pedido atualizado ou None se não existir.
        """
        pedido = self.session.get(PedidoAjuda, pedido_id)
        if pedido is None:
            return None
        pedido.status = payload.status
        self.session.commit()
        self.session.refresh(pedido)
        return pedido
