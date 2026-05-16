"""Repositório de DoadorVoluntario."""

from sqlalchemy.orm import Session

from app.models.doador import DoadorVoluntario
from app.schemas import DoadorCreate, DoadorUpdate


class DoadorRepository:
    """Operações de persistência para `DoadorVoluntario`."""

    def __init__(self, session: Session) -> None:
        """Inicializa o repositório com uma sessão SQLAlchemy.

        Args:
            session: sessão ativa de banco.
        """
        self.session = session

    def create(self, payload: DoadorCreate) -> DoadorVoluntario:
        """Cria e persiste um doador.

        Args:
            payload: dados validados.

        Returns:
            Doador com `id` preenchido.
        """
        doador = DoadorVoluntario(**payload.model_dump())
        self.session.add(doador)
        self.session.commit()
        self.session.refresh(doador)
        return doador

    def get_by_id(self, doador_id: int) -> DoadorVoluntario | None:
        """Busca um doador pelo id.

        Args:
            doador_id: identificador.

        Returns:
            Doador ou None.
        """
        return self.session.get(DoadorVoluntario, doador_id)

    def update(self, doador_id: int, payload: DoadorUpdate) -> DoadorVoluntario | None:
        """Atualiza parcialmente um doador.

        Args:
            doador_id: identificador.
            payload: campos a atualizar.

        Returns:
            Doador atualizado ou None.
        """
        doador = self.session.get(DoadorVoluntario, doador_id)
        if doador is None:
            return None
        for campo, valor in payload.model_dump(exclude_unset=True).items():
            setattr(doador, campo, valor)
        self.session.commit()
        self.session.refresh(doador)
        return doador
