"""Rate limiting por IP usando slowapi.

Expõe um `Limiter` configurado por IP e a função `registrar_rate_limit` que
liga o limiter à aplicação e registra o handler de `429` no formato
ProblemDetail. Os limites são lidos das Settings e podem ser desativados via
`rate_limit_enabled=False` (útil para testes).
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.config import get_settings
from app.core.errors import ProblemDetail
from app.core.request_context import obter_request_id

#: Limiter por IP compartilhado pela aplicação. Os limites de cada rota são
#: resolvidos dinamicamente (callables abaixo) a partir das Settings atuais, e o
#: estado `enabled` é ajustado por `aplicar_estado_limiter` no `create_app`.
limiter = Limiter(key_func=get_remote_address)


def limite_auth() -> str:
    """Retorna o limite configurado para endpoints de autenticação.

    Returns:
        String de limite (ex.: "5/minute") lida de `settings.rate_limit_auth`.
    """
    return get_settings().rate_limit_auth


def limite_criacao() -> str:
    """Retorna o limite configurado para endpoints de criação.

    Returns:
        String de limite lida de `settings.rate_limit_create`.
    """
    return get_settings().rate_limit_create


def limite_contato() -> str:
    """Retorna o limite configurado para a revelação de contato.

    Returns:
        String de limite lida de `settings.rate_limit_contato`.
    """
    return get_settings().rate_limit_contato


def aplicar_estado_limiter() -> None:
    """Sincroniza o flag `enabled` do limiter com as Settings atuais.

    Side Effects:
        Ajusta `limiter.enabled` conforme `settings.rate_limit_enabled`.
    """
    limiter.enabled = get_settings().rate_limit_enabled


async def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Converte `RateLimitExceeded` em uma resposta 429 no formato ProblemDetail.

    Args:
        request: requisição que excedeu o limite.
        exc: exceção levantada pelo slowapi com o limite violado.

    Returns:
        `JSONResponse` 429 (`application/problem+json`).
    """
    request_id = obter_request_id()
    instance = str(request.url.path)
    if request_id:
        instance = f"{instance}#req-{request_id}"
    body = ProblemDetail(
        title="Limite de requisições excedido",
        status=429,
        detail=f"Limite excedido: {exc.detail}. Tente novamente em instantes.",
        instance=instance,
        request_id=request_id or None,
    ).model_dump()
    return JSONResponse(
        status_code=429,
        content=body,
        media_type="application/problem+json",
    )


def registrar_rate_limit(app: FastAPI) -> None:
    """Liga o limiter compartilhado à aplicação e registra o handler de 429.

    Sincroniza o estado `enabled` do limiter com as Settings atuais antes de
    ligá-lo, permitindo desativar o rate limiting em testes via
    `rate_limit_enabled=False`.

    Args:
        app: aplicação FastAPI alvo.

    Side Effects:
        Define `app.state.limiter`, adiciona o `SlowAPIMiddleware` e registra o
        handler de `RateLimitExceeded`.
    """
    aplicar_estado_limiter()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
    app.add_middleware(SlowAPIMiddleware)
