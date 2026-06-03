"""Router REST das estatísticas públicas."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.estatistica_repository import EstatisticaRepository
from app.schemas import EstatisticasRead
from app.services import EstatisticaService

router = APIRouter(prefix="/estatisticas", tags=["estatisticas"])


def _service(db: Session = Depends(get_db)) -> EstatisticaService:
    """Constrói um `EstatisticaService` ligado à sessão corrente.

    Args:
        db: sessão injetada por `get_db`.

    Returns:
        Instância de serviço.
    """
    return EstatisticaService(EstatisticaRepository(db))


@router.get(
    "",
    response_model=EstatisticasRead,
    summary="Estatísticas públicas agregadas",
)
def obter_estatisticas(
    service: EstatisticaService = Depends(_service),
) -> EstatisticasRead:
    """GET /api/v1/estatisticas — contadores públicos do dashboard.

    Ignora pedidos soft-deletados e ocultos pela moderação. Não exige
    autenticação.

    Args:
        service: serviço injetado.

    Returns:
        Contadores agregados de pedidos, status, atendimentos e cidades.
    """
    return EstatisticasRead.model_validate(service.coletar())
