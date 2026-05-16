"""Ponto de entrada da aplicação FastAPI."""

from fastapi import FastAPI

from app.api.health import router as health_router
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
    return application


app = create_app()
