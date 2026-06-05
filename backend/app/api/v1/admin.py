"""Router REST de moderação administrativa (restrito a admin)."""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.database import get_db
from app.models.usuario import Usuario
from app.repositories.denuncia_repository import DenunciaRepository
from app.repositories.doador_repository import DoadorRepository
from app.repositories.pedido_repository import PedidoRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas import DenunciaRead, PedidoRead
from app.services import DenunciaService, UsuarioService

router = APIRouter(prefix="/admin", tags=["admin"])


def _service(db: Session = Depends(get_db)) -> DenunciaService:
    """Constrói um `DenunciaService` ligado à sessão corrente.

    Args:
        db: sessão injetada por `get_db`.

    Returns:
        Instância de serviço.
    """
    return DenunciaService(DenunciaRepository(db), PedidoRepository(db))


def _usuario_service(db: Session = Depends(get_db)) -> UsuarioService:
    """Constrói um `UsuarioService` capaz de anonimizar usuários, pedidos e doador.

    Args:
        db: sessão injetada por `get_db`.

    Returns:
        Serviço de usuário com os repositórios de pedidos e doadores injetados.
    """
    return UsuarioService(
        UsuarioRepository(db),
        pedido_repository=PedidoRepository(db),
        doador_repository=DoadorRepository(db),
    )


@router.get(
    "/denuncias",
    response_model=list[DenunciaRead],
    summary="Lista todas as denúncias (admin)",
)
def listar_denuncias(
    service: DenunciaService = Depends(_service),
    admin: Usuario = Depends(require_admin),
) -> list[DenunciaRead]:
    """GET /api/v1/admin/denuncias — lista denúncias para a moderação.

    Args:
        service: serviço injetado.
        admin: administrador autenticado (exigência de papel).

    Returns:
        Lista de denúncias, das mais recentes para as mais antigas.

    Raises:
        NaoAutenticadoError: se não houver Bearer válido (vira 401).
        AcessoNegadoError: se o usuário não for administrador (vira 403).
    """
    return [DenunciaRead.model_validate(d) for d in service.listar()]


@router.patch(
    "/pedidos/{pedido_id}/ocultar",
    response_model=PedidoRead,
    summary="Oculta um pedido (admin)",
)
def ocultar_pedido(
    pedido_id: int,
    service: DenunciaService = Depends(_service),
    admin: Usuario = Depends(require_admin),
) -> PedidoRead:
    """PATCH /api/v1/admin/pedidos/{id}/ocultar — oculta o pedido do público.

    Args:
        pedido_id: identificador do pedido.
        service: serviço injetado.
        admin: administrador autenticado (exigência de papel).

    Returns:
        Pedido atualizado (com `oculto=True`).

    Raises:
        NaoAutenticadoError: se não houver Bearer válido (vira 401).
        AcessoNegadoError: se o usuário não for administrador (vira 403).
        PedidoNotFoundError: se o pedido não existir (vira 404).
    """
    pedido = service.definir_visibilidade(pedido_id, oculto=True)
    return PedidoRead.model_validate(pedido)


@router.patch(
    "/pedidos/{pedido_id}/reexibir",
    response_model=PedidoRead,
    summary="Reexibe um pedido ocultado (admin)",
)
def reexibir_pedido(
    pedido_id: int,
    service: DenunciaService = Depends(_service),
    admin: Usuario = Depends(require_admin),
) -> PedidoRead:
    """PATCH /api/v1/admin/pedidos/{id}/reexibir — torna o pedido público novamente.

    Args:
        pedido_id: identificador do pedido.
        service: serviço injetado.
        admin: administrador autenticado (exigência de papel).

    Returns:
        Pedido atualizado (com `oculto=False`).

    Raises:
        NaoAutenticadoError: se não houver Bearer válido (vira 401).
        AcessoNegadoError: se o usuário não for administrador (vira 403).
        PedidoNotFoundError: se o pedido não existir (vira 404).
    """
    pedido = service.definir_visibilidade(pedido_id, oculto=False)
    return PedidoRead.model_validate(pedido)


@router.patch(
    "/denuncias/{denuncia_id}/resolver",
    response_model=DenunciaRead,
    summary="Resolve uma denúncia (admin)",
)
def resolver_denuncia(
    denuncia_id: int,
    service: DenunciaService = Depends(_service),
    admin: Usuario = Depends(require_admin),
) -> DenunciaRead:
    """PATCH /api/v1/admin/denuncias/{id}/resolver — marca a denúncia como resolvida.

    Args:
        denuncia_id: identificador da denúncia.
        service: serviço injetado.
        admin: administrador autenticado (exigência de papel).

    Returns:
        Denúncia atualizada (com `status=resolvida`).

    Raises:
        NaoAutenticadoError: se não houver Bearer válido (vira 401).
        AcessoNegadoError: se o usuário não for administrador (vira 403).
        DenunciaNotFoundError: se a denúncia não existir (vira 404).
    """
    denuncia = service.resolver(denuncia_id)
    return DenunciaRead.model_validate(denuncia)


@router.delete(
    "/usuarios/{usuario_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Anonimiza e elimina um usuário por id (admin)",
)
def remover_usuario(
    usuario_id: int,
    service: UsuarioService = Depends(_usuario_service),
    admin: Usuario = Depends(require_admin),
) -> Response:
    """DELETE /api/v1/admin/usuarios/{id} — anonimiza/elimina um usuário (LGPD).

    Aplica o mesmo procedimento do direito de eliminação do titular: anonimiza o
    usuário, marca seu soft-delete e remove (soft-delete) seus pedidos.

    Args:
        usuario_id: identificador do usuário a remover.
        service: serviço injetado (com repositório de pedidos).
        admin: administrador autenticado (exigência de papel).

    Returns:
        Resposta vazia com status 204.

    Raises:
        NaoAutenticadoError: se não houver Bearer válido (vira 401).
        AcessoNegadoError: se o usuário não for administrador (vira 403).
        UsuarioNotFoundError: se o usuário não existir (vira 404).
    """
    service.anonimizar(usuario_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
