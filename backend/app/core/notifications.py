"""Abstração de notificação ao protetor quando um atendimento é registrado.

Define a interface `Notifier` e duas implementações: `LogNotifier` (default,
apenas registra a notificação no logging estruturado, sem efeitos externos) e
`SmtpNotifier` (envia e-mail via `smtplib`). A escolha do backend é feita por
`get_notifier`, a partir de `Settings.notifier_backend`, deixando a costura
pronta para, em produção, ativar o envio de e-mail sem alterar a camada de
serviço/rotas. Inclui também `link_whatsapp`, helper que converte um contato em
URL `wa.me` quando o contato parece um telefone brasileiro.
"""

from __future__ import annotations

import logging
import re
import smtplib
from abc import ABC, abstractmethod
from email.message import EmailMessage

from app.config import Settings, get_settings
from app.models.atendimento import AtendimentoPedido
from app.models.doador import DoadorVoluntario
from app.models.pedido import PedidoAjuda

logger = logging.getLogger(__name__)

#: DDI do Brasil, prefixado aos telefones nacionais sem código de país.
_DDI_BRASIL = "55"
#: Faixa de dígitos plausível para um telefone BR (com ou sem DDI/DDD).
_MIN_DIGITOS_TELEFONE = 10
_MAX_DIGITOS_TELEFONE = 13


class Notifier(ABC):
    """Interface de notificação ao autor de um pedido.

    Implementações concretas decidem o meio de entrega (log, e-mail, etc.). O
    contrato é mínimo e estável para acomodar novos canais sem mudar o serviço.
    """

    @abstractmethod
    def notificar_novo_atendimento(
        self,
        *,
        pedido: PedidoAjuda,
        atendimento: AtendimentoPedido,
        doador: DoadorVoluntario,
    ) -> None:
        """Notifica o protetor (autor do pedido) sobre um novo atendimento.

        Args:
            pedido: pedido que recebeu o atendimento (traz o contato do autor).
            atendimento: atendimento recém-criado (traz o `tipo_ajuda`).
            doador: doador que ofereceu a ajuda (nome e contato).

        Side Effects:
            Depende da implementação (registra log, envia e-mail, etc.). Não
            retorna nada.
        """


def _resumo_atendimento(
    *, pedido: PedidoAjuda, atendimento: AtendimentoPedido, doador: DoadorVoluntario
) -> str:
    """Monta a mensagem PT-BR de notificação de um novo atendimento.

    Args:
        pedido: pedido atendido.
        atendimento: atendimento criado.
        doador: doador que ofereceu ajuda.

    Returns:
        Mensagem legível descrevendo quem ajudou, com qual tipo de ajuda e como
        falar com o doador.
    """
    contato_doador = doador.telefone or doador.email or "contato não informado"
    return (
        f'{doador.nome} ofereceu ajuda do tipo "{atendimento.tipo_ajuda}" '
        f'no seu pedido "{pedido.titulo}". Fale com o doador: {contato_doador}.'
    )


class LogNotifier(Notifier):
    """Notifier que apenas registra a notificação no logging estruturado.

    É o backend default (dev/test): não envia nada externo e não exige segredos.
    """

    def notificar_novo_atendimento(
        self,
        *,
        pedido: PedidoAjuda,
        atendimento: AtendimentoPedido,
        doador: DoadorVoluntario,
    ) -> None:
        """Registra a notificação de novo atendimento via `logging`.

        Args:
            pedido: pedido atendido.
            atendimento: atendimento criado.
            doador: doador que ofereceu ajuda.

        Side Effects:
            Emite um log de nível INFO com os identificadores do pedido, do
            atendimento e do doador. Não envia nada externo.
        """
        logger.info(
            "Notificação de novo atendimento: %s",
            _resumo_atendimento(pedido=pedido, atendimento=atendimento, doador=doador),
            extra={
                "pedido_id": pedido.id,
                "atendimento_id": atendimento.id,
                "doador_id": doador.id,
            },
        )


class SmtpNotifier(Notifier):
    """Notifier que envia a notificação por e-mail via `smtplib`.

    Usa o servidor SMTP configurado em `Settings` (host/port/user/password/
    from/tls). Destinado a produção; em dev/test o backend default é `log`.

    Atributos:
        host: host do servidor SMTP.
        port: porta do servidor SMTP.
        user: usuário de autenticação (ou None).
        password: senha de autenticação (ou None).
        remetente: endereço usado no campo `From`.
        usar_tls: se deve iniciar STARTTLS antes de autenticar/enviar.
    """

    def __init__(
        self,
        *,
        host: str,
        port: int,
        remetente: str,
        user: str | None = None,
        password: str | None = None,
        usar_tls: bool = True,
    ) -> None:
        """Inicializa o backend SMTP.

        Args:
            host: host do servidor SMTP.
            port: porta do servidor SMTP.
            remetente: endereço de e-mail usado como remetente.
            user: usuário de autenticação (opcional).
            password: senha de autenticação (opcional).
            usar_tls: se deve usar STARTTLS (default True).
        """
        self.host = host
        self.port = port
        self.remetente = remetente
        self.user = user
        self.password = password
        self.usar_tls = usar_tls

    def notificar_novo_atendimento(
        self,
        *,
        pedido: PedidoAjuda,
        atendimento: AtendimentoPedido,
        doador: DoadorVoluntario,
    ) -> None:
        """Envia ao contato do pedido um e-mail sobre o novo atendimento.

        Args:
            pedido: pedido atendido (o `contato` do autor é o destinatário).
            atendimento: atendimento criado.
            doador: doador que ofereceu ajuda.

        Side Effects:
            Abre uma conexão SMTP e envia uma mensagem de e-mail. Pode levantar
            exceções de rede/SMTP, que cabe ao chamador tratar.
        """
        mensagem = EmailMessage()
        mensagem["Subject"] = "Seu pedido recebeu uma oferta de ajuda"
        mensagem["From"] = self.remetente
        mensagem["To"] = pedido.contato
        mensagem.set_content(
            _resumo_atendimento(pedido=pedido, atendimento=atendimento, doador=doador)
        )

        with smtplib.SMTP(self.host, self.port) as cliente:
            if self.usar_tls:
                cliente.starttls()
            if self.user and self.password:
                cliente.login(self.user, self.password)
            cliente.send_message(mensagem)


def get_notifier(settings: Settings | None = None) -> Notifier:
    """Factory do `Notifier` a partir das Settings.

    Em dev/test o backend default é `log` (nenhum segredo necessário). O backend
    `smtp` exige host e remetente configurados.

    Args:
        settings: configurações da aplicação; quando None, usa `get_settings()`.

    Returns:
        Instância de `Notifier` pronta para uso.

    Raises:
        ValueError: se `notifier_backend == "smtp"` sem `smtp_host`/`smtp_from`.
    """
    settings = settings or get_settings()
    if settings.notifier_backend == "smtp":
        if not settings.smtp_host or not settings.smtp_from:
            raise ValueError("notifier_backend='smtp' exige SMTP_HOST e SMTP_FROM configurados.")
        return SmtpNotifier(
            host=settings.smtp_host,
            port=settings.smtp_port,
            remetente=settings.smtp_from,
            user=settings.smtp_user,
            password=settings.smtp_password,
            usar_tls=settings.smtp_tls,
        )
    return LogNotifier()


def link_whatsapp(contato: str) -> str | None:
    """Converte um contato em URL `wa.me` quando parece um telefone brasileiro.

    Extrai apenas os dígitos do contato. Se a quantidade de dígitos for plausível
    para um telefone BR, normaliza para incluir o DDI 55 (quando ausente) e
    devolve a URL `https://wa.me/<digitos>`. Contatos que não parecem telefone
    (ex.: e-mails) devolvem None.

    Args:
        contato: forma de contato cadastrada (telefone ou e-mail).

    Returns:
        URL `https://wa.me/<digitos>` quando o contato parece telefone BR; None
        caso contrário.
    """
    if "@" in contato:
        return None

    digitos = re.sub(r"\D", "", contato)
    if not (_MIN_DIGITOS_TELEFONE <= len(digitos) <= _MAX_DIGITOS_TELEFONE):
        return None

    if not digitos.startswith(_DDI_BRASIL) or len(digitos) <= 11:
        digitos = f"{_DDI_BRASIL}{digitos}"

    return f"https://wa.me/{digitos}"
