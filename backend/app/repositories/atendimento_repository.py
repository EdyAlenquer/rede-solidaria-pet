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
        self,
        pedido_id: int,
        payload: AtendimentoCreate,
        *,
        doador_id: int,
        commit: bool = True,
    ) -> AtendimentoPedido:
        """Persiste um novo atendimento vinculado ao pedido e ao doador informados.

        Args:
            pedido_id: id do pedido sendo atendido.
            payload: dados do atendimento (`tipo_ajuda`, `observacao`).
            doador_id: id do doador que registra o atendimento; derivado do
                usuário autenticado pela camada de serviço.
            commit: se True, confirma a transação imediatamente; se False, apenas
                executa flush para permitir composição transacional pelo service.

        Returns:
            Atendimento persistido com `id` e `data_contato`.

        Raises:
            sqlalchemy.exc.IntegrityError: se `pedido_id` ou `doador_id` não existirem
                (com o pragma de FK ativo), ou se já houver atendimento desse doador
                para o pedido (viola `uq_atendimentos_pedido_doador`).
        """
        atendimento = AtendimentoPedido(
            pedido_id=pedido_id,
            doador_id=doador_id,
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

    def list_by_doador(self, doador_id: int) -> list[AtendimentoPedido]:
        """Lista atendimentos de um doador, do mais antigo ao mais recente.

        Usado pela exportação de dados pessoais (LGPD), em que o doador é derivado
        do usuário autenticado pelo e-mail.

        Args:
            doador_id: id do doador.

        Returns:
            Lista de atendimentos registrados pelo doador.
        """
        stmt = (
            select(AtendimentoPedido)
            .where(AtendimentoPedido.doador_id == doador_id)
            .order_by(AtendimentoPedido.data_contato.asc())
        )
        return list(self.session.scalars(stmt).all())
