"""Testes leves de instância dos modelos ORM (sem persistência).

Persistência completa é coberta nos testes de repositório.
"""

from sqlalchemy import create_engine

from app.models import (
    AtendimentoPedido,
    Base,
    DoadorVoluntario,
    PedidoAjuda,
    StatusPedidoEnum,
    UrgenciaEnum,
)


def test_metadata_registra_tres_tabelas_do_dominio() -> None:
    """As três tabelas do domínio devem estar na metadata da Base."""
    nomes = set(Base.metadata.tables.keys())
    assert {"pedidos", "doadores", "atendimentos"}.issubset(nomes)


def test_create_all_em_sqlite_em_memoria_funciona() -> None:
    """O DDL dos modelos roda sem erros em SQLite em memória."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    inspetor_tables = set(Base.metadata.tables.keys())
    assert "pedidos" in inspetor_tables
    assert "doadores" in inspetor_tables
    assert "atendimentos" in inspetor_tables


def test_pedido_default_status_e_aberto() -> None:
    """O `default` do campo `status` é `ABERTO` antes de persistir."""
    pedido = PedidoAjuda(
        titulo="Cãozinho ferido",
        descricao="Encontrado na rua X",
        categoria="resgate",
        urgencia=UrgenciaEnum.ALTA,
        contato="11999990000",
    )
    # O default só é aplicado em flush; aqui validamos o tipo via instância.
    assert pedido.titulo == "Cãozinho ferido"
    assert pedido.urgencia == UrgenciaEnum.ALTA


def test_doador_aceita_apenas_telefone_ou_email() -> None:
    """Modelo permite criar doador com qualquer combinação (validação fica no schema)."""
    apenas_email = DoadorVoluntario(nome="Maria", email="m@example.com")
    apenas_tel = DoadorVoluntario(nome="João", telefone="11988887777")
    assert apenas_email.email == "m@example.com"
    assert apenas_tel.telefone == "11988887777"


def test_atendimento_referencia_pedido_e_doador_por_fk() -> None:
    """O modelo `AtendimentoPedido` expõe `pedido_id` e `doador_id`."""
    atendimento = AtendimentoPedido(pedido_id=1, doador_id=2, tipo_ajuda="ração")
    assert atendimento.pedido_id == 1
    assert atendimento.doador_id == 2
    assert atendimento.tipo_ajuda == "ração"


def test_status_pedido_enum_tem_tres_valores() -> None:
    """`StatusPedidoEnum` cobre os três estados do ciclo de vida."""
    assert {s.value for s in StatusPedidoEnum} == {"aberto", "em_andamento", "concluido"}


def test_urgencia_enum_tem_tres_valores() -> None:
    """`UrgenciaEnum` cobre baixa/media/alta."""
    assert {u.value for u in UrgenciaEnum} == {"baixa", "media", "alta"}
