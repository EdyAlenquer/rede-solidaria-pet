"""Serviço de domínio para DoadorVoluntario."""

from app.core.errors import DoadorNotFoundError
from app.models.doador import DoadorVoluntario
from app.repositories.doador_repository import DoadorRepository
from app.schemas import DoadorCreate


class DoadorService:
    """Operações de negócio sobre DoadorVoluntario."""

    def __init__(self, repository: DoadorRepository) -> None:
        """Inicializa o serviço com um repositório de doadores.

        Args:
            repository: Repositório a ser usado para persistência.
        """
        self.repository = repository

    def create(self, payload: DoadorCreate) -> DoadorVoluntario:
        """Cria um doador.

        Args:
            payload: Dados validados para criação do doador.

        Returns:
            Doador criado com id preenchido.
        """
        return self.repository.create(payload)

    def get_by_id(self, doador_id: int) -> DoadorVoluntario:
        """Busca um doador pelo id.

        Args:
            doador_id: Identificador do doador.

        Returns:
            Doador encontrado.

        Raises:
            DoadorNotFoundError: Se o doador não existir.
        """
        doador = self.repository.get_by_id(doador_id)
        if doador is None:
            raise DoadorNotFoundError(f"Doador id={doador_id} não existe.")
        return doador
