"""Router REST de DoadorVoluntario."""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
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
    summary="Detalha um doador pelo id",
)
def detalhar_doador(
    doador_id: int,
    service: DoadorService = Depends(_service),
) -> DoadorRead:
    """GET /api/v1/doadores/{id} — retorna contato completo administrativo.

    Args:
        doador_id: identificador do doador.
        service: serviço injetado.

    Returns:
        Doador encontrado com telefone e email.

    Raises:
        DoadorNotFoundError: se o doador não existir.
    """
    doador = service.get_by_id(doador_id)
    return DoadorRead.model_validate(doador)
