"""Repositório de PedidoAjuda."""

from dataclasses import dataclass

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.enums import StatusPedidoEnum, UrgenciaEnum
from app.models.pedido import PedidoAjuda
from app.schemas import PedidoCreate, PedidoStatusUpdate, PedidoUpdate


@dataclass(frozen=True)
class PaginatedResult:
    """Resultado paginado de uma listagem de pedidos.

    Attributes:
        items: lista de pedidos na página corrente.
        total: total absoluto após aplicação dos filtros (sem limit/offset).
    """

    items: list[PedidoAjuda]
    total: int


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

    def _apply_filters(self, stmt, *, status, urgencia, categoria, q):
        """Aplica filtros opcionais ao statement SQLAlchemy.

        Args:
            stmt: select() base.
            status: filtra por status (ou None para ignorar).
            urgencia: filtra por urgência (ou None para ignorar).
            categoria: filtra por categoria exata (ou None para ignorar).
            q: substring case-insensitive buscada em titulo/descricao (ou None para ignorar).

        Returns:
            Statement com filtros aplicados.
        """
        if status is not None:
            stmt = stmt.where(PedidoAjuda.status == status)
        if urgencia is not None:
            stmt = stmt.where(PedidoAjuda.urgencia == urgencia)
        if categoria is not None:
            stmt = stmt.where(PedidoAjuda.categoria == categoria)
        if q:
            padrao = f"%{q.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(PedidoAjuda.titulo).like(padrao),
                    func.lower(PedidoAjuda.descricao).like(padrao),
                )
            )
        return stmt

    def list(
        self,
        *,
        status: StatusPedidoEnum | None = None,
        urgencia: UrgenciaEnum | None = None,
        categoria: str | None = None,
        q: str | None = None,
    ) -> list[PedidoAjuda]:
        """Lista pedidos do mais recente para o mais antigo, com filtros opcionais.

        Args:
            status: filtra por status.
            urgencia: filtra por urgência.
            categoria: filtra por categoria (igualdade exata).
            q: substring case-insensitive buscada em titulo/descricao.

        Returns:
            Lista de pedidos ordenada por `data_criacao` desc, `id` desc.
        """
        stmt = select(PedidoAjuda).order_by(PedidoAjuda.data_criacao.desc(), PedidoAjuda.id.desc())
        stmt = self._apply_filters(stmt, status=status, urgencia=urgencia, categoria=categoria, q=q)
        return list(self.session.scalars(stmt).all())

    def list_paginated(
        self,
        *,
        page: int,
        page_size: int,
        status: StatusPedidoEnum | None = None,
        urgencia: UrgenciaEnum | None = None,
        categoria: str | None = None,
        q: str | None = None,
    ) -> PaginatedResult:
        """Lista pedidos com paginação e filtros, retornando também o total.

        Args:
            page: número da página (1-based).
            page_size: tamanho da página.
            status: filtra por status.
            urgencia: filtra por urgência.
            categoria: filtra por categoria (igualdade exata).
            q: substring case-insensitive buscada em titulo/descricao.

        Returns:
            `PaginatedResult` com `items` e `total`.
        """
        offset = max(page - 1, 0) * page_size

        stmt = (
            select(PedidoAjuda)
            .order_by(PedidoAjuda.data_criacao.desc(), PedidoAjuda.id.desc())
            .limit(page_size)
            .offset(offset)
        )
        stmt = self._apply_filters(stmt, status=status, urgencia=urgencia, categoria=categoria, q=q)
        items = list(self.session.scalars(stmt).all())
        total = self.count(status=status, urgencia=urgencia, categoria=categoria, q=q)
        return PaginatedResult(items=items, total=total)

    def count(
        self,
        *,
        status: StatusPedidoEnum | None = None,
        urgencia: UrgenciaEnum | None = None,
        categoria: str | None = None,
        q: str | None = None,
    ) -> int:
        """Conta pedidos aplicando os filtros opcionais.

        Args:
            status: filtra por status.
            urgencia: filtra por urgência.
            categoria: filtra por categoria (igualdade exata).
            q: substring case-insensitive buscada em titulo/descricao.

        Returns:
            Quantidade absoluta de pedidos que satisfazem os filtros.
        """
        stmt = select(func.count(PedidoAjuda.id))
        stmt = self._apply_filters(stmt, status=status, urgencia=urgencia, categoria=categoria, q=q)
        return int(self.session.scalar(stmt) or 0)

    def update(self, pedido_id: int, payload: PedidoUpdate) -> PedidoAjuda | None:
        """Aplica atualização parcial em um pedido.

        Args:
            pedido_id: identificador do pedido alvo.
            payload: campos a atualizar.

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

    def update_status(
        self, pedido_id: int, payload: PedidoStatusUpdate, *, commit: bool = True
    ) -> PedidoAjuda | None:
        """Atualiza somente o status de um pedido.

        Args:
            pedido_id: identificador.
            payload: novo status.
            commit: se True, confirma a transação imediatamente; se False, apenas
                executa flush para permitir composição transacional pelo service.

        Returns:
            Pedido atualizado ou None se não existir.
        """
        pedido = self.session.get(PedidoAjuda, pedido_id)
        if pedido is None:
            return None
        pedido.status = payload.status
        if commit:
            self.session.commit()
        else:
            self.session.flush()
        self.session.refresh(pedido)
        return pedido
