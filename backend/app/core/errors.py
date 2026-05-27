"""Erros de domínio e handlers HTTP padronizados em RFC 7807 (ProblemDetails)."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.exceptions import HTTPException as StarletteHTTPException


class ProblemDetail(BaseModel):
    """Representação RFC 7807 (Problem Details for HTTP APIs) usada em respostas de erro."""

    model_config = ConfigDict(populate_by_name=True)

    type: str = Field(default="about:blank", description="URI que identifica o tipo do erro.")
    title: str = Field(description="Título humano curto do erro.")
    status: int = Field(description="Código HTTP equivalente.")
    detail: str | None = Field(default=None, description="Descrição detalhada do erro.")
    instance: str | None = Field(default=None, description="URI da ocorrência específica.")


class DomainError(Exception):
    """Base de exceções de domínio mapeáveis para ProblemDetail."""

    status_code: int = 500
    title: str = "Internal Server Error"

    def __init__(self, detail: str | None = None) -> None:
        """Inicializa a exceção com um detalhe opcional.

        Args:
            detail: descrição livre.
        """
        super().__init__(detail or self.title)
        self.detail = detail


class PedidoNotFoundError(DomainError):
    """Erro quando um pedido com o id informado não existe."""

    status_code = 404
    title = "Pedido não encontrado"


class DoadorNotFoundError(DomainError):
    """Erro quando um doador com o id informado não existe."""

    status_code = 404
    title = "Doador não encontrado"


class PedidoNotAtendivelError(DomainError):
    """Erro quando um pedido não pode receber novos atendimentos."""

    status_code = 409
    title = "Pedido não pode receber atendimento"


class InvalidStatusTransitionError(DomainError):
    """Erro quando uma transição de status não é permitida pelas regras de negócio."""

    status_code = 409
    title = "Transição de status inválida"


def _problem_response(
    request: Request, status: int, title: str, detail: str | None
) -> JSONResponse:
    """Constrói um JSONResponse no formato ProblemDetail.

    Args:
        request: request corrente (usado para preencher `instance`).
        status: código HTTP.
        title: título humano.
        detail: detalhe opcional.

    Returns:
        Resposta JSON com `content-type: application/problem+json`.
    """
    body = ProblemDetail(
        title=title,
        status=status,
        detail=detail,
        instance=str(request.url.path),
    ).model_dump()
    return JSONResponse(
        status_code=status,
        content=body,
        media_type="application/problem+json",
    )


async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    """Mapeia `DomainError` (e subclasses) para ProblemDetail."""
    return _problem_response(request, exc.status_code, exc.title, exc.detail)


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Mapeia HTTPException padrão para ProblemDetail."""
    detail = exc.detail if isinstance(exc.detail, str) else None
    title = "HTTP Error"
    return _problem_response(request, exc.status_code, title, detail)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Mapeia erros de validação Pydantic para ProblemDetail (422)."""
    return _problem_response(
        request,
        status=422,
        title="Erro de validação",
        detail="; ".join(f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors()),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Registra todos os handlers de exceção da aplicação.

    Args:
        app: instância FastAPI alvo.
    """
    app.add_exception_handler(DomainError, domain_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
