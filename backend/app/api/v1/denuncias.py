"""Router REST de denúncias de pedidos (criação autenticada)."""

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.rate_limit import limite_criacao, limiter
from app.database import get_db
from app.models.usuario import Usuario
from app.repositories.denuncia_repository import DenunciaRepository
from app.repositories.pedido_repository import PedidoRepository
from app.schemas import DenunciaCreate, DenunciaRead
from app.services import DenunciaService

router = APIRouter(prefix="/pedidos/{pedido_id}/denuncias", tags=["denuncias"])


def _service(db: Session = Depends(get_db)) -> DenunciaService:
    """Constrói um `DenunciaService` ligado à sessão corrente.

    Args:
        db: sessão injetada por `get_db`.

    Returns:
        Instância de serviço.
    """
    return DenunciaService(DenunciaRepository(db), PedidoRepository(db))


@router.post(
    "",
    response_model=DenunciaRead,
    status_code=status.HTTP_201_CREATED,
    summary="Denuncia um pedido (requer autenticação)",
)
@limiter.limit(limite_criacao)
def criar_denuncia(
    request: Request,
    pedido_id: int,
    payload: DenunciaCreate,
    response: Response,
    service: DenunciaService = Depends(_service),
    usuario: Usuario = Depends(get_current_user),
) -> DenunciaRead:
    """POST /api/v1/pedidos/{id}/denuncias — registra uma denúncia autenticada.

    Args:
        request: requisição corrente (exigida pelo rate limiter).
        pedido_id: identificador do pedido denunciado.
        payload: dados da denúncia (`motivo`, `descricao`).
        response: usado para definir o header `Location`.
        service: serviço injetado.
        usuario: usuário autenticado (autor da denúncia).

    Returns:
        Denúncia criada.

    Raises:
        NaoAutenticadoError: se não houver Bearer válido (vira 401).
        PedidoNotFoundError: se o pedido não existir (vira 404).
    """
    denuncia = service.criar(pedido_id, payload, autor_id=usuario.id)
    response.headers["Location"] = f"/api/v1/admin/denuncias/{denuncia.id}"
    return DenunciaRead.model_validate(denuncia)
