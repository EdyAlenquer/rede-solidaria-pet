"""Middlewares de observabilidade e hardening HTTP.

Inclui:
    - `RequestIdMiddleware`: gera/propaga `X-Request-Id`, registra o request-id no
      contexto, loga método/rota/status/latência e captura exceções não tratadas.
    - `SecurityHeadersMiddleware`: adiciona headers de segurança em toda resposta
      (nosniff, anti-clickjacking, referrer-policy, CSP e HSTS em produção).
"""

from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.request_context import definir_request_id

#: Nome do header HTTP que carrega o identificador da requisição.
REQUEST_ID_HEADER = "X-Request-Id"

#: Logger usado para emitir o resumo de cada requisição.
_logger = logging.getLogger("app.request")


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Gera/propaga o request-id e loga um resumo estruturado de cada requisição.

    Para cada request:
        - reaproveita o `X-Request-Id` enviado pelo cliente ou gera um UUID4;
        - registra o request-id no contexto (para logging e ProblemDetail);
        - mede a latência e loga método, rota, status e `latencia_ms`;
        - devolve o request-id no header da resposta;
        - loga e re-levanta exceções não tratadas (o handler global responde).
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Processa a requisição aplicando request-id e logging estruturado.

        Args:
            request: requisição HTTP recebida.
            call_next: chamada para o próximo handler da cadeia.

        Returns:
            A resposta HTTP com o header `X-Request-Id`.

        Raises:
            Exception: re-levanta qualquer exceção não tratada do handler após
                logá-la, para que o handler de exceções global a converta em
                ProblemDetail.
        """
        request_id = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex
        definir_request_id(request_id)
        inicio = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            latencia_ms = round((time.perf_counter() - inicio) * 1000, 2)
            _logger.exception(
                "Exceção não tratada na requisição",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "latencia_ms": latencia_ms,
                },
            )
            raise

        latencia_ms = round((time.perf_counter() - inicio) * 1000, 2)
        response.headers[REQUEST_ID_HEADER] = request_id
        _logger.info(
            "Requisição concluída",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "latencia_ms": latencia_ms,
            },
        )
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adiciona headers de segurança em todas as respostas.

    Headers sempre presentes: `X-Content-Type-Options`, `X-Frame-Options`,
    `Referrer-Policy` e um `Content-Security-Policy` conservador. Em produção,
    adiciona também `Strict-Transport-Security` (HSTS).

    O CSP conservador (`default-src 'none'`) é omitido nas rotas de documentação
    (`/docs`, `/redoc`, `/openapi.json`) — que só existem em desenvolvimento —
    para não bloquear o carregamento da UI Swagger/ReDoc no navegador.
    """

    #: Prefixos de rota da documentação onde o CSP restritivo é omitido.
    _DOCS_PATHS = ("/docs", "/redoc", "/openapi.json")

    def __init__(self, app, *, is_production: bool) -> None:
        """Inicializa o middleware.

        Args:
            app: aplicação ASGI envolvida.
            is_production: quando True, habilita o header HSTS.
        """
        super().__init__(app)
        self._is_production = is_production

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Aplica os headers de segurança na resposta.

        Args:
            request: requisição HTTP recebida.
            call_next: chamada para o próximo handler da cadeia.

        Returns:
            A resposta HTTP com os headers de segurança adicionados.
        """
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        if not request.url.path.startswith(self._DOCS_PATHS):
            response.headers.setdefault(
                "Content-Security-Policy",
                "default-src 'none'; frame-ancestors 'none'",
            )
        if self._is_production:
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )
        return response
