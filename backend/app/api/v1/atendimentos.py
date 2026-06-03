"""Router REST de AtendimentoPedido."""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.notifications import get_notifier
from app.core.rate_limit import limite_criacao, limiter
from app.database import get_db
from app.models.usuario import Usuario
from app.repositories.atendimento_repository import AtendimentoRepository
from app.repositories.doador_repository import DoadorRepository
from app.repositories.pedido_repository import PedidoRepository
from app.schemas import AtendimentoCreate, AtendimentoPublicRead
from app.services import AtendimentoService

router = APIRouter(prefix="/pedidos/{pedido_id}/atendimentos", tags=["atendimentos"])


def _service(db: Session = Depends(get_db)) -> AtendimentoService:
    """Constrói um `AtendimentoService` ligado à sessão corrente.

    Args:
        db: sessão injetada por `get_db`.

    Returns:
        Instância de serviço, com o `Notifier` resolvido por `get_notifier`.
    """
    return AtendimentoService(
        AtendimentoRepository(db),
        PedidoRepository(db),
        DoadorRepository(db),
        notifier=get_notifier(),
    )


@router.post(
    "",
    response_model=AtendimentoPublicRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um atendimento para um pedido",
)
@limiter.limit(limite_criacao)
def criar_atendimento(
    request: Request,
    pedido_id: int,
    payload: AtendimentoCreate,
    service: AtendimentoService = Depends(_service),
    usuario: Usuario = Depends(get_current_user),
) -> AtendimentoPublicRead:
    """POST /api/v1/pedidos/{id}/atendimentos — registra atendimento autenticado.

    O doador é derivado do usuário autenticado (find-or-create por e-mail); o
    corpo traz apenas `tipo_ajuda` e `observacao`.

    Args:
        request: requisição corrente (exigida pelo rate limiter).
        pedido_id: identificador do pedido atendido.
        payload: dados do atendimento (`tipo_ajuda`, `observacao`).
        service: serviço injetado.
        usuario: usuário autenticado que registra o atendimento.

    Returns:
        Atendimento criado sem telefone ou email do doador.

    Raises:
        NaoAutenticadoError: se não houver Bearer válido (vira 401).
        PedidoNotFoundError: se o pedido não existir (vira 404).
        PedidoNotAtendivelError: se o pedido estiver concluído/cancelado (vira 409).
        AtendimentoDuplicadoError: se o usuário já atendeu este pedido (vira 409).
    """
    atendimento = service.create(pedido_id, payload, usuario=usuario)
    return AtendimentoPublicRead.model_validate(atendimento)


@router.get(
    "",
    response_model=list[AtendimentoPublicRead],
    summary="Lista atendimentos de um pedido",
)
def listar_atendimentos(
    pedido_id: int,
    service: AtendimentoService = Depends(_service),
) -> list[AtendimentoPublicRead]:
    """GET /api/v1/pedidos/{id}/atendimentos — lista atendimentos públicos.

    Args:
        pedido_id: identificador do pedido.
        service: serviço injetado.

    Returns:
        Lista de atendimentos sem telefone ou email do doador.

    Raises:
        PedidoNotFoundError: se o pedido não existir.
    """
    atendimentos = service.list_by_pedido(pedido_id)
    return [AtendimentoPublicRead.model_validate(atendimento) for atendimento in atendimentos]
