"""Enums do domínio compartilhados entre modelos e schemas."""

import enum


class UrgenciaEnum(enum.StrEnum):
    """Nível de urgência declarado pelo protetor ao criar o pedido."""

    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"


class StatusPedidoEnum(enum.StrEnum):
    """Estado atual do pedido no ciclo de vida."""

    ABERTO = "aberto"
    EM_ANDAMENTO = "em_andamento"
    CONCLUIDO = "concluido"
