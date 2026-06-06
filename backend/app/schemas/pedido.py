"""Schemas Pydantic para PedidoAjuda."""

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import (
    CategoriaEnum,
    EspecieEnum,
    PorteEnum,
    SexoEnum,
    StatusPedidoEnum,
    UrgenciaEnum,
)
from app.schemas.imagem import ImagemRead


class PedidoBase(BaseModel):
    """Campos comuns aos schemas de entrada de pedido.

    Inclui a localização (cidade/estado obrigatórios; bairro e coordenadas
    opcionais) e os atributos opcionais do animal. O `estado` é validado e
    normalizado para a UF de duas letras maiúsculas.
    """

    titulo: str = Field(min_length=3, max_length=120)
    descricao: str = Field(min_length=10)
    categoria: CategoriaEnum
    urgencia: UrgenciaEnum

    # Localização. A validação estrita (cidade não vazia, UF de 2 letras) vive em
    # PedidoCreate (entrada); na LEITURA os campos são tolerantes para serializar
    # pedidos legados com valores vazios deixados pelo backfill da migração.
    cidade: str = Field(max_length=80)
    estado: str = Field(max_length=2)
    bairro: str | None = Field(default=None, max_length=80)
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)

    # Atributos do animal (todos opcionais)
    especie: EspecieEnum | None = None
    porte: PorteEnum | None = None
    sexo: SexoEnum | None = None
    idade_aproximada: str | None = Field(default=None, max_length=40)
    quantidade: int = Field(default=1, ge=1)


class PedidoCreate(PedidoBase):
    """Payload para criação de um pedido.

    Reforça a localização (cidade não vazia, UF de 2 letras) e inclui o `contato`
    (forma de contato do responsável), que é persistido mas nunca exposto na
    leitura pública (`PedidoRead`); exige o aceite explícito do termo de
    consentimento LGPD (`consentimento_aceito=True`).
    """

    cidade: str = Field(min_length=1, max_length=80)
    estado: str = Field(min_length=2, max_length=2)
    contato: str = Field(min_length=5, max_length=120)
    consentimento_aceito: bool = False
    consentimento_versao: str | None = Field(default=None, max_length=20)

    @field_validator("estado")
    @classmethod
    def _valida_uf(cls, valor: str) -> str:
        """Normaliza e valida a sigla da UF na criação.

        Args:
            valor: estado informado (ex.: "sp", "SP").

        Returns:
            UF em maiúsculas com exatamente duas letras (ex.: "SP").

        Raises:
            ValueError: se não forem exatamente duas letras.
        """
        normalizado = valor.strip().upper()
        if len(normalizado) != 2 or not normalizado.isalpha():
            raise ValueError("Informe a UF com duas letras (ex.: SP).")
        return normalizado

    @model_validator(mode="after")
    def _exige_consentimento(self) -> "PedidoCreate":
        """Garante que o termo de consentimento foi aceito.

        Returns:
            A própria instância validada.

        Raises:
            ValueError: se `consentimento_aceito` não for True.
        """
        if not self.consentimento_aceito:
            raise ValueError("É necessário aceitar o termo de consentimento para criar o pedido.")
        return self


class PedidoUpdate(BaseModel):
    """Payload para atualização parcial — campos opcionais.

    Exclui `status`, atualizado por endpoint dedicado.
    """

    titulo: str | None = Field(default=None, min_length=3, max_length=120)
    descricao: str | None = Field(default=None, min_length=10)
    categoria: CategoriaEnum | None = None
    urgencia: UrgenciaEnum | None = None
    contato: str | None = Field(default=None, min_length=5, max_length=120)
    cidade: str | None = Field(default=None, min_length=1, max_length=80)
    estado: str | None = Field(default=None, min_length=2, max_length=2)
    bairro: str | None = Field(default=None, max_length=80)
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)
    especie: EspecieEnum | None = None
    porte: PorteEnum | None = None
    sexo: SexoEnum | None = None
    idade_aproximada: str | None = Field(default=None, max_length=40)
    quantidade: int | None = Field(default=None, ge=1)

    @field_validator("estado")
    @classmethod
    def _valida_uf(cls, valor: str | None) -> str | None:
        """Normaliza e valida a UF quando informada.

        Args:
            valor: estado informado ou None.

        Returns:
            UF normalizada (duas letras maiúsculas) ou None.

        Raises:
            ValueError: se informada e não forem exatamente duas letras.
        """
        if valor is None:
            return None
        normalizado = valor.strip().upper()
        if len(normalizado) != 2 or not normalizado.isalpha():
            raise ValueError("Informe a UF com duas letras (ex.: SP).")
        return normalizado


class PedidoStatusUpdate(BaseModel):
    """Payload exclusivo para mudança de status."""

    status: StatusPedidoEnum


class PedidoContato(BaseModel):
    """Schema de leitura do contato protegido de um pedido.

    Servido apenas em rota autenticada (`GET /pedidos/{id}/contato`), já que o
    `contato` é omitido da leitura pública (`PedidoRead`). Quando o `contato`
    parece um telefone brasileiro, `whatsapp` traz o link `wa.me`
    correspondente; caso contrário, vem nulo.
    """

    contato: str
    whatsapp: str | None = None


class PedidoRead(PedidoBase):
    """Schema de leitura — adiciona campos servidos pelo backend.

    `autor_id` expõe apenas o id do usuário autor (nunca dados pessoais),
    permitindo ao frontend decidir se o usuário atual é o autor e mostrar as
    ações de editar/excluir. É `None` para pedidos antigos sem autor.

    `data_criacao` é normalizada para UTC-aware: o SQLite devolve timestamps
    sem offset, então datetimes ingênuos são interpretados como UTC para
    garantir serialização ISO-8601 com offset (`+00:00`).
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: StatusPedidoEnum
    oculto: bool
    consentimento_aceito: bool
    autor_id: int | None = None
    data_criacao: datetime
    imagens: list[ImagemRead] = Field(default_factory=list)

    @field_validator("data_criacao")
    @classmethod
    def _normaliza_para_utc(cls, valor: datetime) -> datetime:
        """Garante offset explícito (UTC) em `data_criacao`.

        Args:
            valor: timestamp lido do modelo (pode ser ingênuo no SQLite).

        Returns:
            Mesmo instante com `tzinfo` definido (UTC quando ausente).
        """
        if valor.tzinfo is None:
            return valor.replace(tzinfo=UTC)
        return valor


class PedidoMeuRead(PedidoRead):
    """Schema de leitura do próprio pedido — inclui o `contato`.

    Diferente de `PedidoRead` (público, sem contato), este schema é servido
    apenas ao próprio autor na exportação de dados pessoais (LGPD), por isso
    expõe o `contato` que o usuário cadastrou.
    """

    contato: str
