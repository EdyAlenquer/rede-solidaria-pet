"""Modelo ORM do pedido de ajuda."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import (
    CategoriaEnum,
    EspecieEnum,
    PorteEnum,
    SexoEnum,
    StatusPedidoEnum,
    UrgenciaEnum,
)


class PedidoAjuda(Base):
    """Pedido público de ajuda criado por um protetor.

    Atributos:
        id: chave primária.
        titulo: título curto descritivo.
        descricao: detalhamento do pedido.
        categoria: tipo de ajuda (ração, transporte, veterinário, etc.).
        urgencia: nível de urgência declarado.
        status: estado no ciclo de vida (aberto/em_andamento/concluido).
        contato: forma de contato do responsável (telefone ou e-mail).
        cidade: cidade onde o animal se encontra (obrigatório).
        estado: UF de duas letras (obrigatório).
        bairro: bairro/localidade aproximada (opcional).
        latitude: latitude do ponto de referência (opcional).
        longitude: longitude do ponto de referência (opcional).
        especie: espécie do animal (opcional).
        porte: porte do animal (opcional).
        sexo: sexo do animal (opcional).
        idade_aproximada: idade aproximada em texto livre curto (opcional).
        quantidade: número de animais no pedido (>= 1, default 1).
        autor_id: id do usuário autor; FK nullable para `usuarios.id` (pedidos
            antigos podem não ter autor). Indexada para consultas por autoria.
        oculto: marcação de moderação; quando True o pedido é omitido das
            listagens e do detalhe público (default False).
        consentimento_aceito: aceite explícito do termo LGPD (default False).
        consentimento_versao: versão do termo aceito (opcional).
        consentimento_em: instante do aceite (opcional).
        data_criacao: timestamp de criação (UTC, default agora).
        updated_at: timestamp da última alteração (UTC, atualizado a cada update).
        deleted_at: timestamp de soft-delete; `None` enquanto ativo.
        atendimentos: atendimentos vinculados a este pedido.
        imagens: imagens da galeria do pedido, ordenadas por `ordem`.
        autor: usuário autor do pedido (None para pedidos sem autor).
    """

    __tablename__ = "pedidos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    titulo: Mapped[str] = mapped_column(String(120), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    categoria: Mapped[CategoriaEnum] = mapped_column(
        Enum(CategoriaEnum, name="categoria_enum"), nullable=False, index=True
    )
    urgencia: Mapped[UrgenciaEnum] = mapped_column(
        Enum(UrgenciaEnum, name="urgencia_enum"), nullable=False, index=True
    )
    status: Mapped[StatusPedidoEnum] = mapped_column(
        Enum(StatusPedidoEnum, name="status_pedido_enum"),
        nullable=False,
        default=StatusPedidoEnum.ABERTO,
        index=True,
    )
    contato: Mapped[str] = mapped_column(String(120), nullable=False)

    # Localização
    cidade: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    estado: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    bairro: Mapped[str | None] = mapped_column(String(80), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Atributos do animal (todos opcionais)
    especie: Mapped[EspecieEnum | None] = mapped_column(
        Enum(EspecieEnum, name="especie_enum"), nullable=True, index=True
    )
    porte: Mapped[PorteEnum | None] = mapped_column(
        Enum(PorteEnum, name="porte_enum"), nullable=True, index=True
    )
    sexo: Mapped[SexoEnum | None] = mapped_column(Enum(SexoEnum, name="sexo_enum"), nullable=True)
    idade_aproximada: Mapped[str | None] = mapped_column(String(40), nullable=True)
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Autoria — FK nullable para usuarios.id (pedidos antigos podem não ter autor).
    autor_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Moderação — pedidos ocultos não aparecem nas leituras públicas.
    oculto: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("0"), index=True
    )

    # Consentimento LGPD
    consentimento_aceito: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("0")
    )
    consentimento_versao: Mapped[str | None] = mapped_column(String(20), nullable=True)
    consentimento_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    data_criacao: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    atendimentos: Mapped[list["AtendimentoPedido"]] = relationship(  # noqa: F821
        back_populates="pedido",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    imagens: Mapped[list["ImagemPedido"]] = relationship(  # noqa: F821
        back_populates="pedido",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ImagemPedido.ordem",
    )
    autor: Mapped["Usuario | None"] = relationship(  # noqa: F821
        back_populates="pedidos",
        lazy="selectin",
    )
