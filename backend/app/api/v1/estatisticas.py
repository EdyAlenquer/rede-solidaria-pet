"""Router REST das estatísticas públicas."""

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.http_cache import CACHE_CONTROL_PUBLICO
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
    response: Response,
    service: EstatisticaService = Depends(_service),
) -> EstatisticasRead:
    """GET /api/v1/estatisticas — contadores públicos do dashboard.

    Ignora pedidos soft-deletados e ocultos pela moderação. Não exige
    autenticação. Como o conteúdo é público e compartilhado, recebe um
    `Cache-Control` curto (`public, max-age=30`) para aliviar o backend.

    Args:
        response: resposta corrente, usada para definir o `Cache-Control`.
        service: serviço injetado.

    Returns:
        Contadores agregados de pedidos, status, atendimentos e cidades.
    """
    response.headers["Cache-Control"] = CACHE_CONTROL_PUBLICO
    return EstatisticasRead.model_validate(service.coletar())
