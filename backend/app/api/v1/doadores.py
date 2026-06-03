"""Router REST de DoadorVoluntario."""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.database import get_db
from app.models.usuario import Usuario
from app.repositories.doador_repository import DoadorRepository
from app.schemas import DoadorCreate, DoadorRead
from app.services import DoadorService

router = APIRouter(prefix="/doadores", tags=["doadores"])


def _service(db: Session = Depends(get_db)) -> DoadorService:
    """Constrói um `DoadorService` ligado à sessão corrente.

    Args:
        db: sessão injetada por `get_db`.

    Returns:
        Instância de serviço.
    """
    return DoadorService(DoadorRepository(db))


@router.post(
    "",
    response_model=DoadorRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um doador voluntário",
)
def criar_doador(
    payload: DoadorCreate,
    response: Response,
    service: DoadorService = Depends(_service),
) -> DoadorRead:
    """POST /api/v1/doadores — cria um doador para uso administrativo.

    Args:
        payload: dados do doador.
        response: usado para definir o header `Location`.
        service: serviço injetado.

    Returns:
        Doador criado com contato completo.
    """
    doador = service.create(payload)
    response.headers["Location"] = f"/api/v1/doadores/{doador.id}"
    return DoadorRead.model_validate(doador)


@router.get(
    "/{doador_id}",
    response_model=DoadorRead,
    summary="Detalha um doador pelo id (restrito a admin)",
)
def detalhar_doador(
    doador_id: int,
    service: DoadorService = Depends(_service),
    admin: Usuario = Depends(require_admin),
) -> DoadorRead:
    """GET /api/v1/doadores/{id} — retorna contato completo (apenas admin).

    Args:
        doador_id: identificador do doador.
        service: serviço injetado.
        admin: usuário administrador autenticado (exigência de papel).

    Returns:
        Doador encontrado com telefone e email.

    Raises:
        NaoAutenticadoError: se não houver Bearer válido (vira 401).
        AcessoNegadoError: se o usuário não for administrador (vira 403).
        DoadorNotFoundError: se o doador não existir (vira 404).
    """
    doador = service.get_by_id(doador_id)
    return DoadorRead.model_validate(doador)
