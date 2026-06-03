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
    CANCELADO = "cancelado"


class CategoriaEnum(enum.StrEnum):
    """Categoria de ajuda solicitada no pedido.

    Os valores (sem acento) são o contrato compartilhado com o frontend,
    que mantém os rótulos PT-BR exibidos ao usuário.
    """

    RACAO = "racao"
    TRANSPORTE = "transporte"
    VETERINARIO = "veterinario"
    LAR_TEMPORARIO = "lar_temporario"
    RESGATE = "resgate"


class EspecieEnum(enum.StrEnum):
    """Espécie do animal associado ao pedido.

    Os valores (sem acento) compõem o contrato com o frontend, que exibe os
    rótulos PT-BR ao usuário.
    """

    CAO = "cao"
    GATO = "gato"
    OUTRO = "outro"


class PorteEnum(enum.StrEnum):
    """Porte físico aproximado do animal."""

    PEQUENO = "pequeno"
    MEDIO = "medio"
    GRANDE = "grande"


class SexoEnum(enum.StrEnum):
    """Sexo do animal; `DESCONHECIDO` quando não identificado."""

    MACHO = "macho"
    FEMEA = "femea"
    DESCONHECIDO = "desconhecido"


class PapelUsuarioEnum(enum.StrEnum):
    """Papel de um usuário no sistema.

    `PROTETOR` é o papel padrão atribuído no registro; `ADMIN` concede acesso
    a operações de moderação/administração.
    """

    PROTETOR = "protetor"
    ADMIN = "admin"


class MotivoDenunciaEnum(enum.StrEnum):
    """Motivo declarado ao denunciar um pedido."""

    SPAM = "spam"
    GOLPE = "golpe"
    CONTEUDO_IMPROPRIO = "conteudo_improprio"
    OUTRO = "outro"


class StatusDenunciaEnum(enum.StrEnum):
    """Estado de tratamento de uma denúncia pela moderação."""

    ABERTA = "aberta"
    RESOLVIDA = "resolvida"
