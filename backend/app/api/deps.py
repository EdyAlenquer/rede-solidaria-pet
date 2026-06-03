"""Dependências de autorização: extração do usuário a partir do Bearer JWT."""

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import AcessoNegadoError, NaoAutenticadoError
from app.core.security import TokenInvalidoError, decodificar_token
from app.database import get_db
from app.models.enums import PapelUsuarioEnum
from app.models.usuario import Usuario
from app.repositories.usuario_repository import UsuarioRepository

#: Esquema Bearer; `auto_error=False` para que a ausência de credenciais vire
#: um erro de domínio padronizado (ProblemDetail) em vez do 403 default.
_bearer_scheme = HTTPBearer(auto_error=False)


def _carregar_usuario(token: str, db: Session) -> Usuario:
    """Decodifica o token e carrega o usuário ativo correspondente.

    Args:
        token: token JWT (sem prefixo `Bearer`).
        db: sessão de banco.

    Returns:
        Usuário ativo referenciado pelo `sub` do token.

    Raises:
        NaoAutenticadoError: se o token for inválido/expirado, não tiver `sub`
            ou o usuário não existir mais.
    """
    try:
        payload = decodificar_token(token)
    except TokenInvalidoError as exc:
        raise NaoAutenticadoError("Token inválido ou expirado.") from exc

    sub = payload.get("sub")
    if sub is None:
        raise NaoAutenticadoError("Token sem identificação de usuário.")
    try:
        usuario_id = int(sub)
    except (TypeError, ValueError) as exc:
        raise NaoAutenticadoError("Token com identificação de usuário inválida.") from exc

    usuario = UsuarioRepository(db).get_by_id(usuario_id)
    if usuario is None:
        raise NaoAutenticadoError("Usuário do token não encontrado.")
    return usuario


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    """Exige autenticação e retorna o usuário do token Bearer.

    Args:
        credentials: credenciais Bearer extraídas do header `Authorization`.
        db: sessão de banco injetada.

    Returns:
        Usuário autenticado e ativo.

    Raises:
        NaoAutenticadoError: se não houver Bearer válido ou o usuário não existir.
    """
    if credentials is None:
        raise NaoAutenticadoError("Autenticação obrigatória.")
    return _carregar_usuario(credentials.credentials, db)


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> Usuario | None:
    """Retorna o usuário autenticado quando há Bearer válido; senão `None`.

    Diferente de `get_current_user`, a ausência de credenciais não é erro — útil
    para endpoints públicos que enriquecem a resposta quando há sessão.

    Args:
        credentials: credenciais Bearer (opcionais).
        db: sessão de banco injetada.

    Returns:
        Usuário autenticado, ou `None` se não houver credenciais.

    Raises:
        NaoAutenticadoError: se houver credenciais, mas forem inválidas.
    """
    if credentials is None:
        return None
    return _carregar_usuario(credentials.credentials, db)


def require_admin(usuario: Usuario = Depends(get_current_user)) -> Usuario:
    """Exige que o usuário autenticado tenha papel de administrador.

    Args:
        usuario: usuário autenticado (resolvido por `get_current_user`).

    Returns:
        O próprio usuário, quando for `ADMIN`.

    Raises:
        AcessoNegadoError: se o usuário não for administrador.
    """
    if usuario.papel is not PapelUsuarioEnum.ADMIN:
        raise AcessoNegadoError("Acesso restrito a administradores.")
    return usuario
