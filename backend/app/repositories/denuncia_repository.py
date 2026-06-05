"""Repositório de Denuncia (moderação)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.denuncia import Denuncia
from app.models.enums import StatusDenunciaEnum
from app.schemas import DenunciaCreate


class DenunciaRepository:
    """Operações de persistência para `Denuncia`."""

    def __init__(self, session: Session) -> None:
        """Inicializa o repositório com uma sessão SQLAlchemy.

        Args:
            session: sessão ativa de banco.
        """
        self.session = session

    def create(self, pedido_id: int, payload: DenunciaCreate, *, autor_id: int | None) -> Denuncia:
        """Cria e persiste uma denúncia para o pedido informado.

        Args:
            pedido_id: id do pedido denunciado.
            payload: dados da denúncia (`motivo`, `descricao`).
            autor_id: id do usuário denunciante (ou None se anônimo).

        Returns:
            Denúncia recém-criada com `id`, `status` e `criado_em` preenchidos.
        """
        denuncia = Denuncia(
            pedido_id=pedido_id,
            autor_id=autor_id,
            motivo=payload.motivo,
            descricao=payload.descricao,
        )
        self.session.add(denuncia)
        self.session.commit()
        self.session.refresh(denuncia)
        return denuncia

    def get_by_id(self, denuncia_id: int) -> Denuncia | None:
        """Busca uma denúncia pelo id.

        Args:
            denuncia_id: identificador.

        Returns:
            Denúncia encontrada ou None.
        """
        return self.session.get(Denuncia, denuncia_id)

    def list(self) -> list[Denuncia]:
        """Lista todas as denúncias, das mais recentes para as mais antigas.

        Returns:
            Lista de denúncias ordenada por `criado_em` desc, `id` desc.
        """
        stmt = select(Denuncia).order_by(Denuncia.criado_em.desc(), Denuncia.id.desc())
        return list(self.session.scalars(stmt).all())

    def resolver(self, denuncia_id: int) -> Denuncia | None:
        """Marca uma denúncia como resolvida.

        Args:
            denuncia_id: identificador da denúncia.

        Returns:
            Denúncia atualizada, ou None se não existir.
        """
        denuncia = self.get_by_id(denuncia_id)
        if denuncia is None:
            return None
        denuncia.status = StatusDenunciaEnum.RESOLVIDA
        self.session.commit()
        self.session.refresh(denuncia)
        return denuncia
