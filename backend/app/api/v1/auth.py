"""Router REST de autenticação (registro, login e dados do usuário atual)."""

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.errors import CredenciaisInvalidasError
from app.core.rate_limit import limite_auth, limiter
from app.core.security import criar_access_token
from app.database import get_db
from app.models.usuario import Usuario
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas import LoginRequest, TokenResponse, UsuarioCreate, UsuarioRead
from app.services import UsuarioService

router = APIRouter(prefix="/auth", tags=["auth"])


def _service(db: Session = Depends(get_db)) -> UsuarioService:
    """Constrói um `UsuarioService` ligado à sessão corrente.

    Args:
        db: sessão injetada por `get_db`.

    Returns:
        Instância de serviço.
    """
    return UsuarioService(UsuarioRepository(db))


@router.post(
    "/registro",
    response_model=UsuarioRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registra um novo usuário (protetor)",
)
@limiter.limit(limite_auth)
def registrar(
    request: Request,
    payload: UsuarioCreate,
    response: Response,
    service: UsuarioService = Depends(_service),
) -> UsuarioRead:
    """POST /api/v1/auth/registro — cria uma conta de protetor.

    Args:
        request: requisição corrente (exigida pelo rate limiter).
        payload: dados de registro (senha em texto puro, validada).
        response: usado para definir o header `Location`.
        service: serviço injetado.

    Returns:
        Usuário criado (sem senha nem hash).

    Raises:
        EmailJaCadastradoError: se o e-mail já estiver em uso (vira 409).
    """
    usuario = service.create(payload)
    response.headers["Location"] = f"/api/v1/auth/usuarios/{usuario.id}"
    return UsuarioRead.model_validate(usuario)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Autentica e retorna um access token",
)
@limiter.limit(limite_auth)
def login(
    request: Request,
    payload: LoginRequest,
    service: UsuarioService = Depends(_service),
) -> TokenResponse:
    """POST /api/v1/auth/login — valida credenciais e emite um JWT.

    Args:
        request: requisição corrente (exigida pelo rate limiter).
        payload: e-mail e senha do usuário.
        service: serviço injetado.

    Returns:
        Token de acesso (`bearer`).

    Raises:
        CredenciaisInvalidasError: se e-mail/senha forem inválidos (vira 401).
    """
    usuario = service.autenticar(payload.email, payload.senha)
    if usuario is None:
        raise CredenciaisInvalidasError("E-mail ou senha inválidos.")
    token = criar_access_token(sub=str(usuario.id), extra={"papel": usuario.papel.value})
    return TokenResponse(access_token=token)


@router.get(
    "/me",
    response_model=UsuarioRead,
    summary="Retorna o usuário autenticado",
)
def me(usuario: Usuario = Depends(get_current_user)) -> UsuarioRead:
    """GET /api/v1/auth/me — retorna os dados do usuário autenticado.

    Args:
        usuario: usuário resolvido a partir do Bearer JWT.

    Returns:
        Dados públicos do usuário (sem senha nem hash).

    Raises:
        NaoAutenticadoError: se não houver Bearer válido (vira 401).
    """
    return UsuarioRead.model_validate(usuario)
