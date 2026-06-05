"""Router REST de PedidoAjuda."""

import math

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.http_cache import CACHE_CONTROL_PUBLICO
from app.core.notifications import link_whatsapp
from app.core.rate_limit import limite_contato, limite_criacao, limiter
from app.database import get_db
from app.models.enums import (
    CategoriaEnum,
    EspecieEnum,
    PorteEnum,
    StatusPedidoEnum,
    UrgenciaEnum,
)
from app.models.usuario import Usuario
from app.repositories.pedido_repository import PedidoRepository
from app.schemas import (
    PageInfo,
    PedidoContato,
    PedidoCreate,
    PedidoPage,
    PedidoRead,
    PedidoStatusUpdate,
    PedidoUpdate,
)
from app.services.pedido_service import PedidoService

router = APIRouter(prefix="/pedidos", tags=["pedidos"])


def _service(db: Session = Depends(get_db)) -> PedidoService:
    """Constrói um `PedidoService` ligado à sessão corrente.

    Args:
        db: sessão injetada por `get_db`.

    Returns:
        Instância de serviço.
    """
    return PedidoService(PedidoRepository(db))


@router.post(
    "",
    response_model=PedidoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um pedido de ajuda",
)
@limiter.limit(limite_criacao)
def criar_pedido(
    request: Request,
    payload: PedidoCreate,
    response: Response,
    service: PedidoService = Depends(_service),
    usuario: Usuario = Depends(get_current_user),
) -> PedidoRead:
    """POST /api/v1/pedidos — cria um novo pedido autenticado (RF01, RF02).

    Requer autenticação: o pedido criado fica vinculado ao usuário atual como
    autor (`autor_id`).

    Args:
        request: requisição corrente (exigida pelo rate limiter).
        payload: dados do pedido.
        response: usado para definir o header `Location`.
        service: serviço injetado.
        usuario: usuário autenticado (autor do pedido).

    Returns:
        Pedido criado.

    Raises:
        NaoAutenticadoError: se não houver Bearer válido (vira 401).
    """
    pedido = service.create(payload, autor_id=usuario.id)
    response.headers["Location"] = f"/api/v1/pedidos/{pedido.id}"
    return PedidoRead.model_validate(pedido)


@router.get(
    "",
    response_model=PedidoPage,
    summary="Lista pedidos com filtros e paginação",
)
def listar_pedidos(
    response: Response,
    status_filter: StatusPedidoEnum | None = Query(default=None, alias="status"),
    urgencia: UrgenciaEnum | None = Query(default=None),
    categoria: CategoriaEnum | None = Query(default=None),
    cidade: str | None = Query(default=None, max_length=80),
    estado: str | None = Query(default=None, min_length=2, max_length=2),
    especie: EspecieEnum | None = Query(default=None),
    porte: PorteEnum | None = Query(default=None),
    latitude: float | None = Query(default=None, ge=-90.0, le=90.0),
    longitude: float | None = Query(default=None, ge=-180.0, le=180.0),
    q: str | None = Query(default=None, max_length=120),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PedidoPage:
    """GET /api/v1/pedidos — lista paginada com filtros (RF03, RF04).

    A listagem é pública e majoritariamente compartilhada entre visitantes, então
    recebe um `Cache-Control` curto (`public, max-age=30`) para aliviar o backend
    sem servir dados muito desatualizados. Rotas autenticadas não usam esse header.

    Args:
        response: resposta corrente, usada para definir o `Cache-Control`.
        status_filter: filtra por status (query `status`).
        urgencia: filtra por urgência.
        categoria: filtra por categoria.
        cidade: filtra por cidade (igualdade exata).
        estado: filtra por UF (igualdade exata, 2 letras).
        especie: filtra por espécie do animal.
        porte: filtra por porte do animal.
        latitude: latitude do ponto de referência; com `longitude`, ordena por distância.
        longitude: longitude do ponto de referência; com `latitude`, ordena por distância.
        q: busca textual em titulo/descricao.
        page: número da página (1-based).
        page_size: tamanho da página (1..100).
        db: sessão injetada.

    Returns:
        Página de pedidos.
    """
    response.headers["Cache-Control"] = CACHE_CONTROL_PUBLICO
    estado_uf = estado.upper() if estado else None
    repo = PedidoRepository(db)
    resultado = repo.list_paginated(
        page=page,
        page_size=page_size,
        status=status_filter,
        urgencia=urgencia,
        categoria=categoria,
        q=q,
        cidade=cidade,
        estado=estado_uf,
        especie=especie,
        porte=porte,
        latitude=latitude,
        longitude=longitude,
    )
    total_pages = math.ceil(resultado.total / page_size) if resultado.total else 0
    return PedidoPage(
        items=[PedidoRead.model_validate(p) for p in resultado.items],
        page_info=PageInfo(
            page=page, page_size=page_size, total=resultado.total, total_pages=total_pages
        ),
    )


@router.get(
    "/{pedido_id}",
    response_model=PedidoRead,
    summary="Detalha um pedido pelo id",
)
def detalhar_pedido(
    pedido_id: int,
    service: PedidoService = Depends(_service),
) -> PedidoRead:
    """GET /api/v1/pedidos/{id} — detalhe (RF05, RF08).

    Args:
        pedido_id: identificador.
        service: serviço injetado.

    Returns:
        Pedido encontrado.

    Raises:
        PedidoNotFoundError: se o pedido não existir ou estiver oculto (vira 404).
    """
    pedido = service.get_public_by_id(pedido_id)
    return PedidoRead.model_validate(pedido)


@router.get(
    "/{pedido_id}/contato",
    response_model=PedidoContato,
    summary="Revela o contato de um pedido (requer autenticação)",
)
@limiter.limit(limite_contato)
def revelar_contato_pedido(
    request: Request,
    pedido_id: int,
    service: PedidoService = Depends(_service),
    usuario: Usuario = Depends(get_current_user),
) -> PedidoContato:
    """GET /api/v1/pedidos/{id}/contato — revela o contato protegido (RF08).

    A leitura pública (`PedidoRead`) não traz o contato; este endpoint exige
    autenticação para revelá-lo a usuários logados.

    Args:
        request: requisição corrente (exigida pelo rate limiter).
        pedido_id: identificador do pedido.
        service: serviço injetado.
        usuario: usuário autenticado (exigência de autenticação).

    Returns:
        Objeto com o contato do responsável e, quando for telefone BR, o link
        `wa.me` correspondente em `whatsapp`.

    Raises:
        NaoAutenticadoError: se não houver Bearer válido (vira 401).
        PedidoNotFoundError: se o pedido não existir ou estiver oculto (vira 404).
    """
    pedido = service.get_public_by_id(pedido_id)
    return PedidoContato(contato=pedido.contato, whatsapp=link_whatsapp(pedido.contato))


@router.patch(
    "/{pedido_id}",
    response_model=PedidoRead,
    summary="Edita um pedido (somente autor ou admin)",
)
def editar_pedido(
    pedido_id: int,
    payload: PedidoUpdate,
    service: PedidoService = Depends(_service),
    usuario: Usuario = Depends(get_current_user),
) -> PedidoRead:
    """PATCH /api/v1/pedidos/{id} — edição parcial restrita ao autor ou admin.

    Args:
        pedido_id: identificador.
        payload: campos a atualizar (parciais).
        service: serviço injetado.
        usuario: usuário autenticado (deve ser autor ou admin).

    Returns:
        Pedido atualizado.

    Raises:
        NaoAutenticadoError: se não houver Bearer válido (vira 401).
        AcessoNegadoError: se o usuário não for autor nem admin (vira 403).
        PedidoNotFoundError: se o pedido não existir/estiver removido (vira 404).
    """
    pedido = service.update(pedido_id, payload, usuario=usuario)
    return PedidoRead.model_validate(pedido)


@router.delete(
    "/{pedido_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove um pedido (soft-delete; somente autor ou admin)",
)
def excluir_pedido(
    pedido_id: int,
    service: PedidoService = Depends(_service),
    usuario: Usuario = Depends(get_current_user),
) -> Response:
    """DELETE /api/v1/pedidos/{id} — soft-delete restrito ao autor ou admin.

    Args:
        pedido_id: identificador.
        service: serviço injetado.
        usuario: usuário autenticado (deve ser autor ou admin).

    Returns:
        Resposta vazia com status 204.

    Raises:
        NaoAutenticadoError: se não houver Bearer válido (vira 401).
        AcessoNegadoError: se o usuário não for autor nem admin (vira 403).
        PedidoNotFoundError: se o pedido não existir/estiver removido (vira 404).
    """
    service.delete(pedido_id, usuario=usuario)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/{pedido_id}/status",
    response_model=PedidoRead,
    summary="Atualiza o status de um pedido (somente autor ou admin)",
)
def atualizar_status_pedido(
    pedido_id: int,
    payload: PedidoStatusUpdate,
    service: PedidoService = Depends(_service),
    usuario: Usuario = Depends(get_current_user),
) -> PedidoRead:
    """PATCH /api/v1/pedidos/{id}/status — atualiza status (RF06, RF07).

    Restrito ao autor do pedido ou a um administrador.

    Args:
        pedido_id: identificador.
        payload: novo status.
        service: serviço injetado.
        usuario: usuário autenticado (deve ser autor ou admin).

    Returns:
        Pedido atualizado.

    Raises:
        NaoAutenticadoError: se não houver Bearer válido (vira 401).
        AcessoNegadoError: se o usuário não for autor nem admin (vira 403).
        PedidoNotFoundError: se o pedido não existir (vira 404).
        InvalidStatusTransitionError: transição inválida (vira 409).
    """
    pedido = service.change_status(pedido_id, payload, usuario=usuario)
    return PedidoRead.model_validate(pedido)
