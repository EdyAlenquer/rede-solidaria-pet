"""Testes do AtendimentoService (regras de negócio sobre AtendimentoRepository)."""

import pytest
from sqlalchemy.orm import Session

from app.core.errors import (
    AtendimentoDuplicadoError,
    PedidoNotAtendivelError,
    PedidoNotFoundError,
)
from app.models.enums import PapelUsuarioEnum, StatusPedidoEnum, UrgenciaEnum
from app.models.usuario import Usuario
from app.repositories.atendimento_repository import AtendimentoRepository
from app.repositories.doador_repository import DoadorRepository
from app.repositories.pedido_repository import PedidoRepository
from app.schemas import AtendimentoCreate, PedidoCreate, PedidoStatusUpdate
from app.services import AtendimentoService


def _pedido_payload(**overrides) -> PedidoCreate:
    """Constrói um `PedidoCreate` válido para os testes."""
    base = {
        "titulo": "Pedido teste",
        "descricao": "Descrição longa o suficiente para passar.",
        "categoria": "resgate",
        "urgencia": UrgenciaEnum.ALTA,
        "contato": "11999990000",
        "cidade": "São Paulo",
        "estado": "SP",
        "consentimento_aceito": True,
    }
    base.update(overrides)
    return PedidoCreate(**base)


def _criar_usuario(db_session: Session, *, email: str = "doador@example.com") -> Usuario:
    """Cria e persiste um usuário (futuro doador derivado) para os testes.

    Args:
        db_session: sessão de teste.
        email: e-mail do usuário (vira chave do doador derivado).

    Returns:
        Usuário persistido.
    """
    usuario = Usuario(
        nome="Doador Usuário",
        email=email,
        senha_hash="x",
        telefone="11988887777",
        papel=PapelUsuarioEnum.PROTETOR,
        consentimento_aceito=True,
    )
    db_session.add(usuario)
    db_session.commit()
    db_session.refresh(usuario)
    return usuario


def _service(db_session: Session, *, notifier=None) -> AtendimentoService:
    """Constrói o serviço com repositórios reais para a sessão de teste.

    Args:
        db_session: sessão de teste.
        notifier: notifier opcional a injetar (default: o do serviço).

    Returns:
        Instância de `AtendimentoService`.
    """
    kwargs = {} if notifier is None else {"notifier": notifier}
    return AtendimentoService(
        atendimento_repository=AtendimentoRepository(db_session),
        pedido_repository=PedidoRepository(db_session),
        doador_repository=DoadorRepository(db_session),
        **kwargs,
    )


class _NotifierEspiao:
    """Notifier-espião que registra as chamadas recebidas, sem efeitos externos."""

    def __init__(self) -> None:
        """Inicializa o espião com a lista de chamadas vazia."""
        self.chamadas: list[dict] = []

    def notificar_novo_atendimento(self, *, pedido, atendimento, doador) -> None:
        """Registra os argumentos da notificação para inspeção posterior."""
        self.chamadas.append({"pedido": pedido, "atendimento": atendimento, "doador": doador})


class _NotifierQueFalha:
    """Notifier que sempre falha, para validar que a falha não quebra o atendimento."""

    def notificar_novo_atendimento(self, *, pedido, atendimento, doador) -> None:
        """Sempre levanta para simular falha de notificação."""
        raise RuntimeError("falha simulada de notificação")


def test_atendimento_service_eh_exportado_pelo_pacote_de_servicos() -> None:
    """`AtendimentoService` está disponível pelo pacote público de serviços."""
    assert AtendimentoService.__name__ == "AtendimentoService"


def test_create_deriva_doador_do_usuario_e_move_para_em_andamento(db_session: Session) -> None:
    """Criar atendimento deriva o doador do usuário e move o pedido para em_andamento."""
    pedido_repo = PedidoRepository(db_session)
    doador_repo = DoadorRepository(db_session)
    pedido = pedido_repo.create(_pedido_payload())
    usuario = _criar_usuario(db_session)

    atendimento = _service(db_session).create(
        pedido.id, AtendimentoCreate(tipo_ajuda="ração"), usuario=usuario
    )

    assert atendimento.id is not None
    assert pedido_repo.get_by_id(pedido.id).status is StatusPedidoEnum.EM_ANDAMENTO
    # O doador foi criado a partir do e-mail do usuário (find-or-create).
    doador = doador_repo.get_by_email(usuario.email)
    assert doador is not None
    assert atendimento.doador_id == doador.id


def test_create_reaproveita_doador_existente_por_email(db_session: Session) -> None:
    """Atendimentos de um mesmo usuário em pedidos distintos reusam o mesmo doador."""
    pedido_repo = PedidoRepository(db_session)
    doador_repo = DoadorRepository(db_session)
    pedido_a = pedido_repo.create(_pedido_payload())
    pedido_b = pedido_repo.create(_pedido_payload(titulo="Outro pedido"))
    usuario = _criar_usuario(db_session)
    service = _service(db_session)

    at_a = service.create(pedido_a.id, AtendimentoCreate(tipo_ajuda="ração"), usuario=usuario)
    at_b = service.create(pedido_b.id, AtendimentoCreate(tipo_ajuda="transporte"), usuario=usuario)

    assert at_a.doador_id == at_b.doador_id
    assert len([d for d in [doador_repo.get_by_email(usuario.email)] if d]) == 1


def test_create_mantem_pedido_em_andamento(db_session: Session) -> None:
    """Criar atendimento para pedido em_andamento mantém o status atual."""
    pedido_repo = PedidoRepository(db_session)
    pedido = pedido_repo.create(_pedido_payload())
    pedido_repo.update_status(pedido.id, PedidoStatusUpdate(status=StatusPedidoEnum.EM_ANDAMENTO))
    usuario = _criar_usuario(db_session)

    _service(db_session).create(pedido.id, AtendimentoCreate(tipo_ajuda="ração"), usuario=usuario)

    assert pedido_repo.get_by_id(pedido.id).status is StatusPedidoEnum.EM_ANDAMENTO


def test_create_lanca_pedido_not_found_para_pedido_inexistente(db_session: Session) -> None:
    """Criar atendimento para pedido inexistente levanta `PedidoNotFoundError`."""
    usuario = _criar_usuario(db_session)

    with pytest.raises(PedidoNotFoundError):
        _service(db_session).create(9999, AtendimentoCreate(tipo_ajuda="ração"), usuario=usuario)


def test_create_lanca_pedido_not_atendivel_para_pedido_concluido(db_session: Session) -> None:
    """Criar atendimento para pedido concluido levanta `PedidoNotAtendivelError`."""
    pedido_repo = PedidoRepository(db_session)
    pedido = pedido_repo.create(_pedido_payload())
    pedido_repo.update_status(pedido.id, PedidoStatusUpdate(status=StatusPedidoEnum.CONCLUIDO))
    usuario = _criar_usuario(db_session)

    with pytest.raises(PedidoNotAtendivelError):
        _service(db_session).create(
            pedido.id, AtendimentoCreate(tipo_ajuda="ração"), usuario=usuario
        )


def test_create_lanca_pedido_not_atendivel_para_pedido_cancelado(db_session: Session) -> None:
    """Criar atendimento para pedido cancelado levanta `PedidoNotAtendivelError`."""
    pedido_repo = PedidoRepository(db_session)
    pedido = pedido_repo.create(_pedido_payload())
    pedido_repo.update_status(pedido.id, PedidoStatusUpdate(status=StatusPedidoEnum.CANCELADO))
    usuario = _criar_usuario(db_session)

    with pytest.raises(PedidoNotAtendivelError):
        _service(db_session).create(
            pedido.id, AtendimentoCreate(tipo_ajuda="ração"), usuario=usuario
        )


def test_create_atendimento_duplicado_pelo_mesmo_usuario_levanta_409(db_session: Session) -> None:
    """Segundo atendimento do mesmo usuário no pedido levanta `AtendimentoDuplicadoError`."""
    pedido_repo = PedidoRepository(db_session)
    pedido = pedido_repo.create(_pedido_payload())
    usuario = _criar_usuario(db_session)
    service = _service(db_session)
    service.create(pedido.id, AtendimentoCreate(tipo_ajuda="ração"), usuario=usuario)

    with pytest.raises(AtendimentoDuplicadoError):
        service.create(pedido.id, AtendimentoCreate(tipo_ajuda="transporte"), usuario=usuario)


def test_create_desfaz_atendimento_se_atualizacao_de_status_falhar(
    db_session: Session, monkeypatch
) -> None:
    """Falha ao atualizar status não deixa atendimento parcial persistido."""
    pedido_repo = PedidoRepository(db_session)
    atendimento_repo = AtendimentoRepository(db_session)
    pedido = pedido_repo.create(_pedido_payload())
    usuario = _criar_usuario(db_session)

    def _falha_update_status(*args, **kwargs) -> None:
        raise RuntimeError("falha simulada na atualização")

    monkeypatch.setattr(pedido_repo, "update_status", _falha_update_status)

    with pytest.raises(RuntimeError, match="falha simulada"):
        AtendimentoService(
            atendimento_repository=atendimento_repo,
            pedido_repository=pedido_repo,
            doador_repository=DoadorRepository(db_session),
        ).create(pedido.id, AtendimentoCreate(tipo_ajuda="ração"), usuario=usuario)

    db_session.rollback()
    assert atendimento_repo.list_by_pedido(pedido.id) == []


def test_create_notifica_protetor_com_pedido_e_atendimento_certos(db_session: Session) -> None:
    """Após criar o atendimento, o serviço notifica o protetor com o pedido/atendimento certos."""
    pedido_repo = PedidoRepository(db_session)
    pedido = pedido_repo.create(_pedido_payload())
    usuario = _criar_usuario(db_session)
    espiao = _NotifierEspiao()

    atendimento = _service(db_session, notifier=espiao).create(
        pedido.id, AtendimentoCreate(tipo_ajuda="ração"), usuario=usuario
    )

    assert len(espiao.chamadas) == 1
    chamada = espiao.chamadas[0]
    assert chamada["pedido"].id == pedido.id
    assert chamada["atendimento"].id == atendimento.id
    assert chamada["doador"].email == usuario.email


def test_create_continua_201_quando_notificacao_falha(db_session: Session) -> None:
    """Falha do notifier não impede a criação do atendimento (já persistido)."""
    pedido_repo = PedidoRepository(db_session)
    atendimento_repo = AtendimentoRepository(db_session)
    pedido = pedido_repo.create(_pedido_payload())
    usuario = _criar_usuario(db_session)

    atendimento = _service(db_session, notifier=_NotifierQueFalha()).create(
        pedido.id, AtendimentoCreate(tipo_ajuda="ração"), usuario=usuario
    )

    assert atendimento.id is not None
    assert atendimento_repo.list_by_pedido(pedido.id)[0].id == atendimento.id


def test_list_by_pedido_lanca_pedido_not_found_para_pedido_inexistente(
    db_session: Session,
) -> None:
    """Listar atendimentos de pedido inexistente levanta `PedidoNotFoundError`."""
    with pytest.raises(PedidoNotFoundError):
        _service(db_session).list_by_pedido(9999)
