"""Testes unitários da abstração de notificação e do helper de WhatsApp."""

import logging

from app.config import Settings
from app.core.notifications import (
    LogNotifier,
    Notifier,
    SmtpNotifier,
    get_notifier,
    link_whatsapp,
)
from app.models.atendimento import AtendimentoPedido
from app.models.doador import DoadorVoluntario
from app.models.pedido import PedidoAjuda


def _pedido(**overrides) -> PedidoAjuda:
    """Constrói um `PedidoAjuda` mínimo para as notificações."""
    base = {
        "id": 1,
        "titulo": "Cãozinho ferido",
        "contato": "11999990000",
    }
    base.update(overrides)
    return PedidoAjuda(**base)


def _doador(**overrides) -> DoadorVoluntario:
    """Constrói um `DoadorVoluntario` mínimo para as notificações."""
    base = {"id": 1, "nome": "Maria Silva", "telefone": "11988887777"}
    base.update(overrides)
    return DoadorVoluntario(**base)


def _atendimento(**overrides) -> AtendimentoPedido:
    """Constrói um `AtendimentoPedido` mínimo para as notificações."""
    base = {"id": 1, "pedido_id": 1, "doador_id": 1, "tipo_ajuda": "transporte"}
    base.update(overrides)
    return AtendimentoPedido(**base)


def test_get_notifier_default_e_log() -> None:
    """`get_notifier` com Settings default devolve um `LogNotifier`."""
    notifier = get_notifier(Settings())

    assert isinstance(notifier, LogNotifier)
    assert isinstance(notifier, Notifier)


def test_get_notifier_smtp_quando_backend_smtp() -> None:
    """`get_notifier` devolve `SmtpNotifier` quando o backend é "smtp"."""
    settings = Settings(
        notifier_backend="smtp",
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_from="alertas@example.com",
    )

    notifier = get_notifier(settings)

    assert isinstance(notifier, SmtpNotifier)


def test_log_notifier_registra_notificacao(caplog) -> None:
    """`LogNotifier` registra a notificação via logging estruturado, sem enviar nada."""
    notifier = LogNotifier()
    pedido = _pedido()
    atendimento = _atendimento()
    doador = _doador()

    with caplog.at_level(logging.INFO, logger="app.core.notifications"):
        notifier.notificar_novo_atendimento(pedido=pedido, atendimento=atendimento, doador=doador)

    assert any("atendimento" in registro.message.lower() for registro in caplog.records)


def test_link_whatsapp_com_telefone_br_retorna_url() -> None:
    """`link_whatsapp` devolve uma URL wa.me com DDI 55 para telefone BR."""
    assert link_whatsapp("11999990000") == "https://wa.me/5511999990000"


def test_link_whatsapp_preserva_ddi_quando_presente() -> None:
    """`link_whatsapp` não duplica o DDI 55 quando o contato já o inclui."""
    assert link_whatsapp("+55 (11) 99999-0000") == "https://wa.me/5511999990000"


def test_link_whatsapp_com_email_retorna_none() -> None:
    """`link_whatsapp` devolve None quando o contato é um e-mail."""
    assert link_whatsapp("protetor@example.com") is None


def test_link_whatsapp_com_texto_curto_retorna_none() -> None:
    """`link_whatsapp` devolve None quando não há dígitos suficientes para um telefone."""
    assert link_whatsapp("123") is None
