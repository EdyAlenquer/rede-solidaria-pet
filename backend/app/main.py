"""Ponto de entrada da aplicação FastAPI."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.v1.admin import router as admin_router
from app.api.v1.atendimentos import router as atendimentos_router
from app.api.v1.auth import router as auth_router
from app.api.v1.denuncias import router as denuncias_router
from app.api.v1.doadores import router as doadores_router
from app.api.v1.estatisticas import router as estatisticas_router
from app.api.v1.me import router as me_router
from app.api.v1.pedidos import router as pedidos_router
from app.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configurar_logging
from app.core.middleware import RequestIdMiddleware, SecurityHeadersMiddleware
from app.core.rate_limit import registrar_rate_limit

#: Métodos HTTP liberados pelo CORS (sem coringa `*`).
_CORS_ALLOW_METHODS = ["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"]

#: Headers de requisição liberados pelo CORS (sem coringa `*`).
_CORS_ALLOW_HEADERS = ["Content-Type", "Authorization"]


def create_app() -> FastAPI:
    """Cria e configura a aplicação FastAPI.

    Aplica logging estruturado, middlewares de observabilidade e hardening
    (request-id, security headers), rate limiting por IP e, em produção,
    desabilita a documentação interativa (`/docs`, `/redoc`, `/openapi.json`).

    Returns:
        Instância de FastAPI pronta para servir.
    """
    settings = get_settings()
    configurar_logging(settings.log_level)
    is_production = settings.app_env == "production"

    docs_kwargs: dict[str, str | None] = {}
    if is_production:
        docs_kwargs = {"docs_url": None, "redoc_url": None, "openapi_url": None}

    application = FastAPI(
        title="Rede Solidária Pet API",
        version="0.1.0",
        description="API da plataforma Rede Solidária Pet.",
        **docs_kwargs,
    )

    allowed_origins = settings.allowed_cors_origins()
    if allowed_origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=_CORS_ALLOW_METHODS,
            allow_headers=_CORS_ALLOW_HEADERS,
        )

    application.add_middleware(SecurityHeadersMiddleware, is_production=is_production)
    application.add_middleware(RequestIdMiddleware)
    registrar_rate_limit(application)

    register_exception_handlers(application)
    application.include_router(health_router)
    application.include_router(auth_router, prefix="/api/v1")
    application.include_router(me_router, prefix="/api/v1")
    application.include_router(pedidos_router, prefix="/api/v1")
    application.include_router(denuncias_router, prefix="/api/v1")
    application.include_router(doadores_router, prefix="/api/v1")
    application.include_router(atendimentos_router, prefix="/api/v1")
    application.include_router(estatisticas_router, prefix="/api/v1")
    application.include_router(admin_router, prefix="/api/v1")
    return application


app = create_app()
