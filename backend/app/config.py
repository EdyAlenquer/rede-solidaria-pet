"""Configurações da aplicação carregadas a partir de variáveis de ambiente."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

#: Valor padrão da chave de assinatura JWT, seguro apenas para desenvolvimento.
#: Em produção o uso deste valor é bloqueado por `Settings.secret_key_efetiva`.
#: Tem ≥32 bytes para satisfazer o tamanho mínimo recomendado de chave HS256.
DEFAULT_SECRET_KEY = "dev-insecure-troque-em-producao-change-me"


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

    # Autenticação / JWT
    secret_key: str = Field(default=DEFAULT_SECRET_KEY)
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=60 * 24)

    # Rate limiting (slowapi)
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_auth: str = Field(default="5/minute")
    rate_limit_create: str = Field(default="30/minute")
    rate_limit_contato: str = Field(default="30/minute")

    # Upload de imagens
    #: Diretório onde o `LocalStorageBackend` grava os arquivos enviados.
    #: Em produção, troque por um backend de object storage (Cloudinary/R2).
    upload_dir: str = Field(default="uploads")
    #: Prefixo público sob o qual os arquivos são servidos (StaticFiles).
    public_upload_path: str = Field(default="/uploads")
    #: Tamanho máximo aceito por imagem, em bytes (default 5 MiB).
    max_upload_bytes: int = Field(default=5 * 1024 * 1024)
    #: Content-types de imagem aceitos no upload.
    allowed_image_types: frozenset[str] = Field(
        default=frozenset({"image/jpeg", "image/png", "image/webp"})
    )
    #: Número máximo de imagens por pedido.
    max_imagens_por_pedido: int = Field(default=6)

    # Notificações
    #: Backend de notificação ao protetor quando um atendimento é registrado.
    #: "log" (default): apenas registra a notificação no logging estruturado, sem
    #: enviar nada externo (seguro em dev/test). "smtp": envia e-mail via SMTP.
    notifier_backend: str = Field(default="log")
    #: Host do servidor SMTP (obrigatório quando `notifier_backend == "smtp"`).
    smtp_host: str | None = Field(default=None)
    #: Porta do servidor SMTP (default 587, submissão com STARTTLS).
    smtp_port: int = Field(default=587)
    #: Usuário de autenticação SMTP (opcional).
    smtp_user: str | None = Field(default=None)
    #: Senha de autenticação SMTP (opcional).
    smtp_password: str | None = Field(default=None)
    #: Remetente dos e-mails de notificação (obrigatório quando backend "smtp").
    smtp_from: str | None = Field(default=None)
    #: Usa STARTTLS na conexão SMTP (default True).
    smtp_tls: bool = Field(default=True)

    def allowed_cors_origins(self) -> list[str]:
        """Retorna as origens CORS permitidas.

        As origens são derivadas exclusivamente da variável de ambiente
        `CORS_ORIGINS` (lista separada por vírgulas). Em produção, configure a
        origem do frontend nessa variável (ex.: no `render.yaml`).

        Returns:
            Lista de origens sem espaços e sem valores vazios.
        """
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def secret_key_efetiva(self) -> str:
        """Retorna a chave de assinatura JWT validada para o ambiente atual.

        Em produção, recusa-se a operar com o `secret_key` default inseguro,
        falhando de forma clara para evitar assinaturas previsíveis.

        Returns:
            Chave de assinatura a ser usada por `app.core.security`.

        Raises:
            RuntimeError: se `app_env == "production"` e `secret_key` ainda for
                o valor default inseguro.
        """
        if self.app_env == "production" and self.secret_key == DEFAULT_SECRET_KEY:
            raise RuntimeError(
                "SECRET_KEY default inseguro em produção: defina uma SECRET_KEY própria."
            )
        return self.secret_key


@lru_cache
def get_settings() -> Settings:
    """Retorna a instância memoizada de Settings.

    Returns:
        Configurações da aplicação.
    """
    return Settings()
