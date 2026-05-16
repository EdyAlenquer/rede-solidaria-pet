"""Router de health-check."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Retorna status do serviço.

    Returns:
        Dict com chave `status` igual a `"ok"` quando o serviço está saudável.
    """
    return {"status": "ok"}
