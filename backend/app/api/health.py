"""Router de health-check: liveness (`/health`) e readiness (`/ready`)."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.errors import ProblemDetail
from app.database import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness estático: indica que o processo está de pé.

    Não toca em dependências externas (banco, etc.); serve para orquestradores
    decidirem se o container precisa ser reiniciado.

    Returns:
        Dict com chave `status` igual a `"ok"`.
    """
    return {"status": "ok"}


@router.get("/ready")
def ready(request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    """Readiness: indica que a aplicação consegue atender requests.

    Executa um `SELECT 1` na sessão injetada por `get_db` para confirmar que o
    banco responde. Serve para orquestradores decidirem se podem rotear tráfego.

    Args:
        request: request corrente, usado para preencher `instance` no erro.
        db: sessão SQLAlchemy injetada por `get_db`.

    Returns:
        `JSONResponse` 200 com `{"status": "ready"}` quando o banco responde, ou
        503 no formato ProblemDetail (`application/problem+json`) quando o
        `SELECT 1` falha.
    """
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        body = ProblemDetail(
            title="Serviço indisponível",
            status=503,
            detail=f"Banco de dados indisponível: {exc.__class__.__name__}.",
            instance=str(request.url.path),
        ).model_dump()
        return JSONResponse(
            status_code=503,
            content=body,
            media_type="application/problem+json",
        )
    return JSONResponse(status_code=200, content={"status": "ready"})
