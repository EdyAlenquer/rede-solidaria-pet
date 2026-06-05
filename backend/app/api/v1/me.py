"""Router REST dos direitos do titular (LGPD): exportação e eliminação de dados."""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.usuario import Usuario
from app.repositories.atendimento_repository import AtendimentoRepository
from app.repositories.doador_repository import DoadorRepository
from app.repositories.pedido_repository import PedidoRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas import MeusDadosRead
from app.services import UsuarioService

router = APIRouter(prefix="/me", tags=["me"])


def _service(db: Session = Depends(get_db)) -> UsuarioService:
    """Constrói um `UsuarioService` com todos os repositórios LGPD ligados à sessão.

    Args:
        db: sessão injetada por `get_db`.

    Returns:
        Serviço de usuário com pedido/atendimento/doador injetados.
    """
    return UsuarioService(
        UsuarioRepository(db),
        pedido_repository=PedidoRepository(db),
        atendimento_repository=AtendimentoRepository(db),
        doador_repository=DoadorRepository(db),
    )


@router.get(
    "/dados",
    response_model=MeusDadosRead,
    summary="Exporta os dados pessoais do usuário atual (LGPD)",
)
def exportar_meus_dados(
    service: UsuarioService = Depends(_service),
    usuario: Usuario = Depends(get_current_user),
) -> MeusDadosRead:
    """GET /api/v1/me/dados — exporta os dados pessoais do titular (direito de acesso).

    Args:
        service: serviço injetado (com repositórios de pedidos/atendimentos).
        usuario: usuário autenticado (titular dos dados).

    Returns:
        Estrutura com `perfil`, `pedidos` (com contato próprio) e `atendimentos`.

    Raises:
        NaoAutenticadoError: se não houver Bearer válido (vira 401).
    """
    dados = service.exportar_dados(usuario)
    return MeusDadosRead.model_validate(dados)


@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Anonimiza e elimina a conta do usuário atual (LGPD)",
)
def eliminar_minha_conta(
    service: UsuarioService = Depends(_service),
    usuario: Usuario = Depends(get_current_user),
) -> Response:
    """DELETE /api/v1/me — anonimiza/elimina o titular e seus pedidos (direito de eliminação).

    Após a operação, o token do usuário deixa de autenticar (conta soft-deletada).

    Args:
        service: serviço injetado.
        usuario: usuário autenticado (titular a ser eliminado).

    Returns:
        Resposta vazia com status 204.

    Raises:
        NaoAutenticadoError: se não houver Bearer válido (vira 401).
    """
    service.anonimizar(usuario.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
