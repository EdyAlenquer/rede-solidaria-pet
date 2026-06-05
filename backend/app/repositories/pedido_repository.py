"""Repositório de PedidoAjuda."""

from __future__ import annotations

from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.enums import CategoriaEnum, EspecieEnum, PorteEnum, StatusPedidoEnum, UrgenciaEnum
from app.models.pedido import PedidoAjuda
from app.schemas import PedidoCreate, PedidoStatusUpdate, PedidoUpdate

_RAIO_TERRA_KM = 6371.0


def _distancia_haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula a distância em km entre dois pontos pela fórmula de Haversine.

    Args:
        lat1: latitude do primeiro ponto, em graus.
        lon1: longitude do primeiro ponto, em graus.
        lat2: latitude do segundo ponto, em graus.
        lon2: longitude do segundo ponto, em graus.

    Returns:
        Distância em quilômetros entre os dois pontos.
    """
    rlat1, rlon1, rlat2, rlon2 = (radians(v) for v in (lat1, lon1, lat2, lon2))
    dlat = rlat2 - rlat1
    dlon = rlon2 - rlon1
    a = sin(dlat / 2) ** 2 + cos(rlat1) * cos(rlat2) * sin(dlon / 2) ** 2
    return 2 * _RAIO_TERRA_KM * asin(sqrt(a))


@dataclass(frozen=True)
class PaginatedResult:
    """Resultado paginado de uma listagem de pedidos.

    Attributes:
        items: lista de pedidos na página corrente.
        total: total absoluto após aplicação dos filtros (sem limit/offset).
    """

    items: list[PedidoAjuda]
    total: int


class PedidoRepository:
    """Operações de persistência para `PedidoAjuda`."""

    def __init__(self, session: Session) -> None:
        """Inicializa o repositório com uma sessão SQLAlchemy.

        Args:
            session: sessão ativa de banco.
        """
        self.session = session

    def create(self, payload: PedidoCreate, *, autor_id: int | None = None) -> PedidoAjuda:
        """Cria e persiste um pedido a partir do payload.

        Args:
            payload: dados validados do pedido.
            autor_id: id do usuário autor do pedido; `None` para pedidos sem
                autor. Definido pela camada de API a partir do usuário autenticado.

        Returns:
            Pedido recém-criado com `id` e `data_criacao` preenchidos.
        """
        pedido = PedidoAjuda(**payload.model_dump(), autor_id=autor_id)
        self.session.add(pedido)
        self.session.commit()
        self.session.refresh(pedido)
        return pedido

    def get_by_id(self, pedido_id: int) -> PedidoAjuda | None:
        """Busca um pedido ativo (não soft-deletado) pelo id, incluindo ocultos.

        Usado por fluxos internos/administrativos (edição, autorização, moderação),
        que precisam acessar pedidos ocultos. Para leitura pública use
        `get_public_by_id`.

        Args:
            pedido_id: identificador.

        Returns:
            Pedido encontrado e ativo, ou None se inexistente/soft-deletado.
        """
        pedido = self.session.get(PedidoAjuda, pedido_id)
        if pedido is None or pedido.deleted_at is not None:
            return None
        return pedido

    def get_public_by_id(self, pedido_id: int) -> PedidoAjuda | None:
        """Busca um pedido para leitura pública (ativo e não oculto) pelo id.

        Args:
            pedido_id: identificador.

        Returns:
            Pedido ativo e não oculto, ou None se inexistente/soft-deletado/oculto.
        """
        pedido = self.get_by_id(pedido_id)
        if pedido is None or pedido.oculto:
            return None
        return pedido

    def _apply_filters(
        self,
        stmt,
        *,
        status,
        urgencia,
        categoria,
        q,
        cidade=None,
        estado=None,
        especie=None,
        porte=None,
    ):
        """Aplica filtros opcionais ao statement SQLAlchemy.

        Sempre exclui pedidos soft-deletados (`deleted_at IS NULL`) e ocultos
        pela moderação (`oculto IS False`), garantindo que as listagens públicas
        nunca exponham pedidos removidos ou ocultados.

        Args:
            stmt: select() base.
            status: filtra por status (ou None para ignorar).
            urgencia: filtra por urgência (ou None para ignorar).
            categoria: filtra por categoria exata (ou None para ignorar).
            q: substring case-insensitive buscada em titulo/descricao (ou None para ignorar).
            cidade: filtra por cidade (igualdade exata, ou None para ignorar).
            estado: filtra por UF (igualdade exata, ou None para ignorar).
            especie: filtra por espécie do animal (ou None para ignorar).
            porte: filtra por porte do animal (ou None para ignorar).

        Returns:
            Statement com filtros aplicados.
        """
        stmt = stmt.where(PedidoAjuda.deleted_at.is_(None), PedidoAjuda.oculto.is_(False))
        if status is not None:
            stmt = stmt.where(PedidoAjuda.status == status)
        if urgencia is not None:
            stmt = stmt.where(PedidoAjuda.urgencia == urgencia)
        if categoria is not None:
            stmt = stmt.where(PedidoAjuda.categoria == categoria)
        if cidade is not None:
            stmt = stmt.where(PedidoAjuda.cidade == cidade)
        if estado is not None:
            stmt = stmt.where(PedidoAjuda.estado == estado)
        if especie is not None:
            stmt = stmt.where(PedidoAjuda.especie == especie)
        if porte is not None:
            stmt = stmt.where(PedidoAjuda.porte == porte)
        if q:
            padrao = f"%{q.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(PedidoAjuda.titulo).like(padrao),
                    func.lower(PedidoAjuda.descricao).like(padrao),
                )
            )
        return stmt

    def _ordena_por_distancia(
        self, itens: list[PedidoAjuda], latitude: float, longitude: float
    ) -> list[PedidoAjuda]:
        """Ordena pedidos pela distância ao ponto de referência (mais perto primeiro).

        Pedidos sem coordenadas vão para o fim da lista, preservando a ordem
        relativa original (estável) entre eles.

        Args:
            itens: pedidos já filtrados.
            latitude: latitude do ponto de referência, em graus.
            longitude: longitude do ponto de referência, em graus.

        Returns:
            Nova lista ordenada por distância crescente.
        """

        def _chave(pedido: PedidoAjuda) -> float:
            if pedido.latitude is None or pedido.longitude is None:
                return float("inf")
            return _distancia_haversine_km(latitude, longitude, pedido.latitude, pedido.longitude)

        return sorted(itens, key=_chave)

    def list(
        self,
        *,
        status: StatusPedidoEnum | None = None,
        urgencia: UrgenciaEnum | None = None,
        categoria: CategoriaEnum | None = None,
        q: str | None = None,
        cidade: str | None = None,
        estado: str | None = None,
        especie: EspecieEnum | None = None,
        porte: PorteEnum | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> list[PedidoAjuda]:
        """Lista pedidos do mais recente para o mais antigo, com filtros opcionais.

        Quando `latitude` e `longitude` são informados como ponto de referência,
        a ordenação final passa a ser por distância (Haversine) crescente,
        calculada em Python após a busca.

        Args:
            status: filtra por status.
            urgencia: filtra por urgência.
            categoria: filtra por categoria (igualdade exata).
            q: substring case-insensitive buscada em titulo/descricao.
            cidade: filtra por cidade (igualdade exata).
            estado: filtra por UF (igualdade exata).
            especie: filtra por espécie do animal.
            porte: filtra por porte do animal.
            latitude: latitude do ponto de referência para ordenar por distância.
            longitude: longitude do ponto de referência para ordenar por distância.

        Returns:
            Lista de pedidos ordenada por `data_criacao` desc, `id` desc — ou
            por distância crescente quando há ponto de referência.
        """
        stmt = select(PedidoAjuda).order_by(PedidoAjuda.data_criacao.desc(), PedidoAjuda.id.desc())
        stmt = self._apply_filters(
            stmt,
            status=status,
            urgencia=urgencia,
            categoria=categoria,
            q=q,
            cidade=cidade,
            estado=estado,
            especie=especie,
            porte=porte,
        )
        itens = list(self.session.scalars(stmt).all())
        if latitude is not None and longitude is not None:
            return self._ordena_por_distancia(itens, latitude, longitude)
        return itens

    def list_paginated(
        self,
        *,
        page: int,
        page_size: int,
        status: StatusPedidoEnum | None = None,
        urgencia: UrgenciaEnum | None = None,
        categoria: CategoriaEnum | None = None,
        q: str | None = None,
        cidade: str | None = None,
        estado: str | None = None,
        especie: EspecieEnum | None = None,
        porte: PorteEnum | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> PaginatedResult:
        """Lista pedidos com paginação e filtros, retornando também o total.

        Quando `latitude` e `longitude` são informados, a página é recortada
        sobre o conjunto inteiro ordenado por distância (Haversine), já que a
        ordenação por proximidade é feita em Python.

        Args:
            page: número da página (1-based).
            page_size: tamanho da página.
            status: filtra por status.
            urgencia: filtra por urgência.
            categoria: filtra por categoria (igualdade exata).
            q: substring case-insensitive buscada em titulo/descricao.
            cidade: filtra por cidade (igualdade exata).
            estado: filtra por UF (igualdade exata).
            especie: filtra por espécie do animal.
            porte: filtra por porte do animal.
            latitude: latitude do ponto de referência para ordenar por distância.
            longitude: longitude do ponto de referência para ordenar por distância.

        Returns:
            `PaginatedResult` com `items` e `total`.
        """
        total = self.count(
            status=status,
            urgencia=urgencia,
            categoria=categoria,
            q=q,
            cidade=cidade,
            estado=estado,
            especie=especie,
            porte=porte,
        )
        offset = max(page - 1, 0) * page_size

        if latitude is not None and longitude is not None:
            ordenado = self.list(
                status=status,
                urgencia=urgencia,
                categoria=categoria,
                q=q,
                cidade=cidade,
                estado=estado,
                especie=especie,
                porte=porte,
                latitude=latitude,
                longitude=longitude,
            )
            return PaginatedResult(items=ordenado[offset : offset + page_size], total=total)

        stmt = (
            select(PedidoAjuda)
            .order_by(PedidoAjuda.data_criacao.desc(), PedidoAjuda.id.desc())
            .limit(page_size)
            .offset(offset)
        )
        stmt = self._apply_filters(
            stmt,
            status=status,
            urgencia=urgencia,
            categoria=categoria,
            q=q,
            cidade=cidade,
            estado=estado,
            especie=especie,
            porte=porte,
        )
        items = list(self.session.scalars(stmt).all())
        return PaginatedResult(items=items, total=total)

    def count(
        self,
        *,
        status: StatusPedidoEnum | None = None,
        urgencia: UrgenciaEnum | None = None,
        categoria: CategoriaEnum | None = None,
        q: str | None = None,
        cidade: str | None = None,
        estado: str | None = None,
        especie: EspecieEnum | None = None,
        porte: PorteEnum | None = None,
    ) -> int:
        """Conta pedidos aplicando os filtros opcionais.

        Args:
            status: filtra por status.
            urgencia: filtra por urgência.
            categoria: filtra por categoria (igualdade exata).
            q: substring case-insensitive buscada em titulo/descricao.
            cidade: filtra por cidade (igualdade exata).
            estado: filtra por UF (igualdade exata).
            especie: filtra por espécie do animal.
            porte: filtra por porte do animal.

        Returns:
            Quantidade absoluta de pedidos que satisfazem os filtros.
        """
        stmt = select(func.count(PedidoAjuda.id))
        stmt = self._apply_filters(
            stmt,
            status=status,
            urgencia=urgencia,
            categoria=categoria,
            q=q,
            cidade=cidade,
            estado=estado,
            especie=especie,
            porte=porte,
        )
        return int(self.session.scalar(stmt) or 0)

    def update(self, pedido_id: int, payload: PedidoUpdate) -> PedidoAjuda | None:
        """Aplica atualização parcial em um pedido.

        Args:
            pedido_id: identificador do pedido alvo.
            payload: campos a atualizar.

        Returns:
            Pedido atualizado ou None se não existir (ou estiver soft-deletado).
        """
        pedido = self.get_by_id(pedido_id)
        if pedido is None:
            return None
        for campo, valor in payload.model_dump(exclude_unset=True).items():
            setattr(pedido, campo, valor)
        self.session.commit()
        self.session.refresh(pedido)
        return pedido

    def update_status(
        self, pedido_id: int, payload: PedidoStatusUpdate, *, commit: bool = True
    ) -> PedidoAjuda | None:
        """Atualiza somente o status de um pedido.

        Args:
            pedido_id: identificador.
            payload: novo status.
            commit: se True, confirma a transação imediatamente; se False, apenas
                executa flush para permitir composição transacional pelo service.

        Returns:
            Pedido atualizado ou None se não existir (ou estiver soft-deletado).
        """
        pedido = self.get_by_id(pedido_id)
        if pedido is None:
            return None
        pedido.status = payload.status
        if commit:
            self.session.commit()
        else:
            self.session.flush()
        self.session.refresh(pedido)
        return pedido

    def set_oculto(self, pedido_id: int, oculto: bool) -> PedidoAjuda | None:
        """Define a marcação de moderação `oculto` de um pedido ativo.

        Args:
            pedido_id: identificador do pedido.
            oculto: novo valor da marcação (True oculta, False reexibe).

        Returns:
            Pedido atualizado, ou None se inexistente/soft-deletado.
        """
        pedido = self.get_by_id(pedido_id)
        if pedido is None:
            return None
        pedido.oculto = oculto
        self.session.commit()
        self.session.refresh(pedido)
        return pedido

    def list_by_autor(self, autor_id: int) -> list[PedidoAjuda]:
        """Lista os pedidos ativos de um autor, do mais recente ao mais antigo.

        Inclui pedidos ocultos pela moderação (visão do próprio autor), mas exclui
        os já soft-deletados. Usado pela exportação de dados pessoais (LGPD).

        Args:
            autor_id: id do usuário autor.

        Returns:
            Lista de pedidos ativos do autor.
        """
        stmt = (
            select(PedidoAjuda)
            .where(PedidoAjuda.autor_id == autor_id, PedidoAjuda.deleted_at.is_(None))
            .order_by(PedidoAjuda.data_criacao.desc(), PedidoAjuda.id.desc())
        )
        return list(self.session.scalars(stmt).all())

    def soft_delete_e_anonimizar_por_autor(self, autor_id: int, *, commit: bool = True) -> int:
        """Soft-deleta e anonimiza o contato dos pedidos ativos de um autor.

        Aplica o direito de eliminação (LGPD) aos pedidos do usuário removido:
        marca `deleted_at` e substitui o `contato` por um valor anônimo, de modo
        que nenhum dado pessoal de contato permaneça acessível.

        Args:
            autor_id: id do usuário autor cujos pedidos serão removidos.
            commit: se True, confirma a transação; se False, apenas faz flush
                para permitir composição transacional pela camada de serviço.

        Returns:
            Quantidade de pedidos afetados.

        Side Effects:
            Altera `deleted_at` e `contato` dos pedidos ativos do autor.
        """
        pedidos = self.list_by_autor(autor_id)
        for pedido in pedidos:
            pedido.deleted_at = func.now()
            pedido.contato = "contato removido"
        if commit:
            self.session.commit()
        else:
            self.session.flush()
        return len(pedidos)

    def soft_delete(self, pedido_id: int) -> bool:
        """Marca um pedido como removido (soft-delete) sem apagá-lo do banco.

        Preenche `deleted_at` com o instante atual. Operação idempotente: um
        pedido já soft-deletado (ou inexistente) não é alterado.

        Args:
            pedido_id: identificador do pedido a remover.

        Returns:
            True se o pedido ativo foi marcado como removido; False se não
            existir ou já estiver soft-deletado.
        """
        pedido = self.get_by_id(pedido_id)
        if pedido is None:
            return False
        pedido.deleted_at = func.now()
        self.session.commit()
        return True
