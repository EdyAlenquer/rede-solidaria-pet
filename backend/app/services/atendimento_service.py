"""Serviço de domínio para AtendimentoPedido."""

import logging

from sqlalchemy.exc import IntegrityError

from app.core.errors import (
    AtendimentoDuplicadoError,
    PedidoNotAtendivelError,
    PedidoNotFoundError,
)
from app.core.notifications import Notifier, get_notifier
from app.models.atendimento import AtendimentoPedido
from app.models.doador import DoadorVoluntario
from app.models.enums import StatusPedidoEnum
from app.models.pedido import PedidoAjuda
from app.models.usuario import Usuario
from app.repositories.atendimento_repository import AtendimentoRepository
from app.repositories.doador_repository import DoadorRepository
from app.repositories.pedido_repository import PedidoRepository
from app.schemas import AtendimentoCreate, PedidoStatusUpdate

logger = logging.getLogger(__name__)

#: Status em que um pedido não aceita novos atendimentos.
_STATUS_NAO_ATENDIVEIS = frozenset({StatusPedidoEnum.CONCLUIDO, StatusPedidoEnum.CANCELADO})


class AtendimentoService:
    """Operações de negócio sobre AtendimentoPedido."""

    def __init__(
        self,
        atendimento_repository: AtendimentoRepository,
        pedido_repository: PedidoRepository,
        doador_repository: DoadorRepository,
        notifier: Notifier | None = None,
    ) -> None:
        """Inicializa o serviço com os repositórios necessários.

        Args:
            atendimento_repository: Repositório usado para persistir atendimentos.
            pedido_repository: Repositório usado para consultar e atualizar pedidos.
            doador_repository: Repositório usado para validar doadores.
            notifier: Notifier usado para avisar o protetor após um atendimento
                bem-sucedido. Quando None, usa o backend de `get_notifier()`.
        """
        self.atendimento_repository = atendimento_repository
        self.pedido_repository = pedido_repository
        self.doador_repository = doador_repository
        self.notifier = notifier or get_notifier()

    def create(
        self, pedido_id: int, payload: AtendimentoCreate, *, usuario: Usuario
    ) -> AtendimentoPedido:
        """Cria um atendimento autenticado para um pedido atendível, atomicamente.

        O doador é derivado do usuário autenticado (find-or-create por e-mail),
        evitando doadores órfãos. A criação do doador, do atendimento e a eventual
        transição `aberto -> em_andamento` ocorrem na mesma transação.

        Args:
            pedido_id: Identificador do pedido que receberá o atendimento.
            payload: Dados do atendimento (`tipo_ajuda`, `observacao`).
            usuario: Usuário autenticado que registra o atendimento.

        Returns:
            Atendimento criado.

        Raises:
            PedidoNotFoundError: Se o pedido não existir.
            PedidoNotAtendivelError: Se o pedido estiver concluído ou cancelado.
            AtendimentoDuplicadoError: Se o usuário já tiver um atendimento neste pedido.
        """
        pedido = self.pedido_repository.get_by_id(pedido_id)
        if pedido is None:
            raise PedidoNotFoundError(f"Pedido id={pedido_id} não existe.")

        if pedido.status in _STATUS_NAO_ATENDIVEIS:
            raise PedidoNotAtendivelError(
                f"Pedido id={pedido_id} está {pedido.status.value} e não pode "
                "receber atendimento."
            )

        try:
            doador = self.doador_repository.find_or_create_by_email(
                nome=usuario.nome,
                email=usuario.email,
                telefone=usuario.telefone,
                consentimento_aceito=usuario.consentimento_aceito,
                consentimento_versao=usuario.consentimento_versao,
                consentimento_em=usuario.consentimento_em,
                commit=False,
            )
            atendimento = self.atendimento_repository.create(
                pedido_id, payload, doador_id=doador.id, commit=False
            )
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
        except IntegrityError as exc:
            self.atendimento_repository.session.rollback()
            raise AtendimentoDuplicadoError(
                "Você já registrou um atendimento para este pedido."
            ) from exc
        except Exception:
            self.atendimento_repository.session.rollback()
            raise

        # O atendimento já está persistido: notificar é um efeito colateral
        # best-effort que nunca deve quebrar a operação principal.
        self._notificar_protetor(pedido=pedido, atendimento=atendimento, doador=doador)
        return atendimento

    def _notificar_protetor(
        self,
        *,
        pedido: PedidoAjuda,
        atendimento: AtendimentoPedido,
        doador: DoadorVoluntario,
    ) -> None:
        """Notifica o protetor sobre o novo atendimento, sem propagar falhas.

        Chamado apenas após o commit bem-sucedido. Qualquer erro de notificação
        é registrado em log e absorvido: o atendimento já foi persistido e não
        deve ser revertido por uma falha de efeito colateral.

        Args:
            pedido: pedido atendido (traz o contato do autor).
            atendimento: atendimento recém-criado.
            doador: doador derivado do usuário autenticado.

        Side Effects:
            Aciona o `Notifier` configurado; em caso de exceção, apenas loga.
        """
        try:
            self.notifier.notificar_novo_atendimento(
                pedido=pedido, atendimento=atendimento, doador=doador
            )
        except Exception:
            logger.exception(
                "Falha ao notificar protetor do pedido id=%s sobre o atendimento id=%s",
                pedido.id,
                atendimento.id,
            )

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
