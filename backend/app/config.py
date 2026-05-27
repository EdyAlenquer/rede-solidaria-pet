"""Configurações da aplicação carregadas a partir de variáveis de ambiente."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PRODUCTION_CORS_ORIGINS = ("https://frontend-edyalenquers-projects.vercel.app",)


class Settings(BaseSettings):
    """Configurações tipadas da aplicação.

    Lê variáveis de ambiente (com fallback para `.env`) e expõe
    chaves usadas por outros módulos. Use `get_settings()` para obter
    uma instância memoizada.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="Rede Solidária Pet API")
    app_env: str = Field(default="development")
    log_level: str = Field(default="INFO")
    database_url: str = Field(default="sqlite:///./rede_solidaria_pet.db")
    cors_origins: str = Field(default="")

    def allowed_cors_origins(self) -> list[str]:
        """Retorna as origens CORS permitidas.

        Returns:
            Lista de origens sem espaços e sem valores vazios.
        """
        origins = [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        if self.app_env == "production":
            origins.extend(origin for origin in PRODUCTION_CORS_ORIGINS if origin not in origins)
        return origins


@lru_cache
def get_settings() -> Settings:
    """Retorna a instância memoizada de Settings.

    Returns:
        Configurações da aplicação.
    """
    return Settings()
