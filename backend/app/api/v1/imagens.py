"""Router REST de imagens de um pedido (upload/listagem/remoção)."""

from fastapi import APIRouter, Depends, File, Request, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.config import Settings, get_settings
from app.core.rate_limit import limite_criacao, limiter
from app.core.storage import get_storage
from app.database import get_db
from app.models.usuario import Usuario
from app.repositories.imagem_repository import ImagemRepository
from app.repositories.pedido_repository import PedidoRepository
from app.schemas import ImagemRead
from app.services import ImagemService

router = APIRouter(prefix="/pedidos/{pedido_id}/imagens", tags=["imagens"])


def _service(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ImagemService:
    """Constrói um `ImagemService` ligado à sessão e ao storage configurado.

    Args:
        db: sessão injetada por `get_db`.
        settings: configurações da aplicação (limites e backend de storage).

    Returns:
        Instância de serviço de imagens.
    """
    return ImagemService(
        ImagemRepository(db),
        PedidoRepository(db),
        storage=get_storage(settings),
        settings=settings,
    )


@router.post(
    "",
    response_model=ImagemRead,
    status_code=status.HTTP_201_CREATED,
    summary="Envia uma imagem para um pedido (somente autor ou admin)",
)
@limiter.limit(limite_criacao)
async def enviar_imagem(
    request: Request,
    pedido_id: int,
    arquivo: UploadFile = File(..., description="Arquivo de imagem (jpeg, png ou webp)."),
    service: ImagemService = Depends(_service),
    usuario: Usuario = Depends(get_current_user),
) -> ImagemRead:
    """POST /api/v1/pedidos/{id}/imagens — envia uma imagem para o pedido.

    Restrito ao autor do pedido ou a um administrador. Valida content-type,
    tamanho e o limite de imagens por pedido antes de gravar no storage.

    Args:
        request: requisição corrente (exigida pelo rate limiter).
        pedido_id: identificador do pedido que receberá a imagem.
        arquivo: arquivo de imagem enviado via multipart (campo `arquivo`).
        service: serviço injetado.
        usuario: usuário autenticado (deve ser autor ou admin).

    Returns:
        Imagem criada (`ImagemRead`).

    Raises:
        NaoAutenticadoError: se não houver Bearer válido (vira 401).
        PedidoNotFoundError: se o pedido não existir (vira 404).
        AcessoNegadoError: se o usuário não for autor nem admin (vira 403).
        TipoImagemInvalidoError: content-type não suportado (vira 415).
        ImagemMuitoGrandeError: arquivo excede o tamanho máximo (vira 413).
        LimiteImagensExcedidoError: pedido já tem o máximo de imagens (vira 409).
    """
    conteudo = await arquivo.read()
    content_type = arquivo.content_type or ""
    imagem = service.create(pedido_id, conteudo, content_type, usuario=usuario)
    return ImagemRead.model_validate(imagem)


@router.get(
    "",
    response_model=list[ImagemRead],
    summary="Lista as imagens de um pedido",
)
def listar_imagens(
    pedido_id: int,
    service: ImagemService = Depends(_service),
) -> list[ImagemRead]:
    """GET /api/v1/pedidos/{id}/imagens — lista pública das imagens do pedido.

    Args:
        pedido_id: identificador do pedido.
        service: serviço injetado.

    Returns:
        Lista de imagens ordenadas por `ordem`.

    Raises:
        PedidoNotFoundError: se o pedido não existir (vira 404).
    """
    imagens = service.list_by_pedido(pedido_id)
    return [ImagemRead.model_validate(imagem) for imagem in imagens]


@router.delete(
    "/{imagem_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove uma imagem do pedido (somente autor ou admin)",
)
def remover_imagem(
    pedido_id: int,
    imagem_id: int,
    service: ImagemService = Depends(_service),
    usuario: Usuario = Depends(get_current_user),
) -> Response:
    """DELETE /api/v1/pedidos/{id}/imagens/{imagem_id} — remove imagem do pedido.

    Restrito ao autor do pedido ou a um administrador. Remove o arquivo do
    storage e a linha correspondente.

    Args:
        pedido_id: identificador do pedido dono da imagem.
        imagem_id: identificador da imagem.
        service: serviço injetado.
        usuario: usuário autenticado (deve ser autor ou admin).

    Returns:
        Resposta vazia com status 204.

    Raises:
        NaoAutenticadoError: se não houver Bearer válido (vira 401).
        PedidoNotFoundError: se o pedido não existir (vira 404).
        AcessoNegadoError: se o usuário não for autor nem admin (vira 403).
        ImagemNotFoundError: se a imagem não existir no pedido (vira 404).
    """
    service.delete(pedido_id, imagem_id, usuario=usuario)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
