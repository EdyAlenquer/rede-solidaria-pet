"""Router REST de AtendimentoPedido."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
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
        Instância de serviço.
    """
    return AtendimentoService(
        AtendimentoRepository(db),
        PedidoRepository(db),
        DoadorRepository(db),
    )


@router.post(
    "",
    response_model=AtendimentoPublicRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um atendimento para um pedido",
)
def criar_atendimento(
    pedido_id: int,
    payload: AtendimentoCreate,
    service: AtendimentoService = Depends(_service),
) -> AtendimentoPublicRead:
    """POST /api/v1/pedidos/{id}/atendimentos — registra atendimento público.

    Args:
        pedido_id: identificador do pedido atendido.
        payload: dados do atendimento, incluindo `doador_id`.
        service: serviço injetado.

    Returns:
        Atendimento criado sem telefone ou email do doador.

    Raises:
        PedidoNotFoundError: se o pedido não existir.
        DoadorNotFoundError: se o doador não existir.
        PedidoNotAtendivelError: se o pedido estiver concluído.
    """
    atendimento = service.create(pedido_id, payload)
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
