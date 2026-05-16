"""Router REST de PedidoAjuda."""

import math

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.enums import StatusPedidoEnum, UrgenciaEnum
from app.repositories.pedido_repository import PedidoRepository
from app.schemas import PageInfo, PedidoCreate, PedidoPage, PedidoRead
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
def criar_pedido(
    payload: PedidoCreate,
    response: Response,
    service: PedidoService = Depends(_service),
) -> PedidoRead:
    """POST /api/v1/pedidos — cria um novo pedido (RF01, RF02).

    Args:
        payload: dados do pedido.
        response: usado para definir o header `Location`.
        service: serviço injetado.

    Returns:
        Pedido criado.
    """
    pedido = service.create(payload)
    response.headers["Location"] = f"/api/v1/pedidos/{pedido.id}"
    return PedidoRead.model_validate(pedido)


@router.get(
    "",
    response_model=PedidoPage,
    summary="Lista pedidos com filtros e paginação",
)
def listar_pedidos(
    status_filter: StatusPedidoEnum | None = Query(default=None, alias="status"),
    urgencia: UrgenciaEnum | None = Query(default=None),
    categoria: str | None = Query(default=None, min_length=1, max_length=60),
    q: str | None = Query(default=None, max_length=120),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PedidoPage:
    """GET /api/v1/pedidos — lista paginada com filtros (RF03, RF04).

    Args:
        status_filter: filtra por status (query `status`).
        urgencia: filtra por urgência.
        categoria: filtra por categoria.
        q: busca textual em titulo/descricao.
        page: número da página (1-based).
        page_size: tamanho da página (1..100).
        db: sessão injetada.

    Returns:
        Página de pedidos.
    """
    repo = PedidoRepository(db)
    resultado = repo.list_paginated(
        page=page,
        page_size=page_size,
        status=status_filter,
        urgencia=urgencia,
        categoria=categoria,
        q=q,
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
        PedidoNotFoundError: se o pedido não existir (vira 404 via handler).
    """
    pedido = service.get_by_id(pedido_id)
    return PedidoRead.model_validate(pedido)
