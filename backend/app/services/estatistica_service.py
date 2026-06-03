"""Serviço de domínio para estatísticas agregadas."""

from app.repositories.estatistica_repository import (
    EstatisticaRepository,
    EstatisticasResultado,
)


class EstatisticaService:
    """Operações de negócio sobre estatísticas públicas."""

    def __init__(self, repository: EstatisticaRepository) -> None:
        """Inicializa o serviço com um repositório de estatísticas.

        Args:
            repository: repositório usado para coletar os contadores.
        """
        self.repository = repository

    def coletar(self) -> EstatisticasResultado:
        """Coleta os contadores agregados do dashboard público.

        Returns:
            `EstatisticasResultado` com os contadores agregados.
        """
        return self.repository.coletar()
