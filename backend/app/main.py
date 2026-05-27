"""Ponto de entrada da aplicação FastAPI."""

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.v1.atendimentos import router as atendimentos_router
from app.api.v1.doadores import router as doadores_router
from app.api.v1.pedidos import router as pedidos_router
from app.core.errors import register_exception_handlers


def create_app() -> FastAPI:
    """Cria e configura a aplicação FastAPI.

    Returns:
        Instância de FastAPI pronta para servir.
    """
    application = FastAPI(
        title="Rede Solidária Pet API",
        version="0.1.0",
        description="API da plataforma Rede Solidária Pet.",
    )
    register_exception_handlers(application)
    application.include_router(health_router)
    application.include_router(pedidos_router, prefix="/api/v1")
    application.include_router(doadores_router, prefix="/api/v1")
    application.include_router(atendimentos_router, prefix="/api/v1")
    return application


app = create_app()
