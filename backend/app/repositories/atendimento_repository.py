"""Repositório de AtendimentoPedido."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.atendimento import AtendimentoPedido
from app.schemas import AtendimentoCreate


class AtendimentoRepository:
    """Operações de persistência para `AtendimentoPedido`."""

    def __init__(self, session: Session) -> None:
        """Inicializa o repositório com uma sessão.

        Args:
            session: sessão SQLAlchemy ativa.
        """
        self.session = session

    def create(
        self, pedido_id: int, payload: AtendimentoCreate, *, commit: bool = True
    ) -> AtendimentoPedido:
        """Persiste um novo atendimento vinculado ao pedido informado.

        Args:
            pedido_id: id do pedido sendo atendido.
            payload: dados do atendimento (inclui `doador_id`).
            commit: se True, confirma a transação imediatamente; se False, apenas
                executa flush para permitir composição transacional pelo service.

        Returns:
            Atendimento persistido com `id` e `data_contato`.

        Raises:
            sqlalchemy.exc.IntegrityError: se `pedido_id` ou `doador_id` não existirem
                e o pragma de FK estiver ativo.
        """
        atendimento = AtendimentoPedido(
            pedido_id=pedido_id,
            doador_id=payload.doador_id,
            tipo_ajuda=payload.tipo_ajuda,
            observacao=payload.observacao,
        )
        self.session.add(atendimento)
        if commit:
            self.session.commit()
        else:
            self.session.flush()
        self.session.refresh(atendimento)
        return atendimento

    def list_by_pedido(self, pedido_id: int) -> list[AtendimentoPedido]:
        """Lista atendimentos de um pedido, do mais antigo ao mais recente.

        Args:
            pedido_id: id do pedido.

        Returns:
            Lista de atendimentos.
        """
        stmt = (
            select(AtendimentoPedido)
            .where(AtendimentoPedido.pedido_id == pedido_id)
            .order_by(AtendimentoPedido.data_contato.asc())
        )
        return list(self.session.scalars(stmt).all())
