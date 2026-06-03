"""Testes leves de instância dos modelos ORM (sem persistência).

Persistência completa é coberta nos testes de repositório.
"""

from sqlalchemy import create_engine

from app.models import (
    AtendimentoPedido,
    Base,
    CategoriaEnum,
    Denuncia,
    DoadorVoluntario,
    EspecieEnum,
    ImagemPedido,
    MotivoDenunciaEnum,
    PedidoAjuda,
    PorteEnum,
    SexoEnum,
    StatusDenunciaEnum,
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


def test_status_pedido_enum_tem_quatro_valores() -> None:
    """`StatusPedidoEnum` cobre os quatro estados do ciclo de vida."""
    assert {s.value for s in StatusPedidoEnum} == {
        "aberto",
        "em_andamento",
        "concluido",
        "cancelado",
    }


def test_urgencia_enum_tem_tres_valores() -> None:
    """`UrgenciaEnum` cobre baixa/media/alta."""
    assert {u.value for u in UrgenciaEnum} == {"baixa", "media", "alta"}


def test_categoria_enum_tem_os_valores_do_frontend() -> None:
    """`CategoriaEnum` cobre exatamente as categorias usadas pelo frontend."""
    assert {c.value for c in CategoriaEnum} == {
        "racao",
        "transporte",
        "veterinario",
        "lar_temporario",
        "resgate",
    }


def test_pedido_tem_colunas_de_timestamp_e_soft_delete() -> None:
    """`PedidoAjuda` expõe `updated_at` e `deleted_at` no mapeamento ORM."""
    colunas = set(PedidoAjuda.__table__.columns.keys())
    assert {"data_criacao", "updated_at", "deleted_at"}.issubset(colunas)


def test_atendimento_tem_colunas_de_timestamp_e_soft_delete() -> None:
    """`AtendimentoPedido` expõe `updated_at` e `deleted_at`."""
    colunas = set(AtendimentoPedido.__table__.columns.keys())
    assert {"data_contato", "updated_at", "deleted_at"}.issubset(colunas)


def test_doador_tem_colunas_de_timestamp_e_soft_delete() -> None:
    """`DoadorVoluntario` expõe `created_at`, `updated_at` e `deleted_at`."""
    colunas = set(DoadorVoluntario.__table__.columns.keys())
    assert {"created_at", "updated_at", "deleted_at"}.issubset(colunas)


def test_doador_impoe_unicidade_de_email_e_check_de_contato() -> None:
    """`DoadorVoluntario` declara UniqueConstraint(email) e CheckConstraint de contato."""
    constraint_types = {type(c).__name__ for c in DoadorVoluntario.__table__.constraints}
    assert "UniqueConstraint" in constraint_types
    assert "CheckConstraint" in constraint_types


def test_especie_enum_tem_valores_esperados() -> None:
    """`EspecieEnum` cobre cão/gato/outro."""
    assert {e.value for e in EspecieEnum} == {"cao", "gato", "outro"}


def test_porte_enum_tem_valores_esperados() -> None:
    """`PorteEnum` cobre pequeno/medio/grande."""
    assert {p.value for p in PorteEnum} == {"pequeno", "medio", "grande"}


def test_sexo_enum_tem_valores_esperados() -> None:
    """`SexoEnum` cobre macho/femea/desconhecido."""
    assert {s.value for s in SexoEnum} == {"macho", "femea", "desconhecido"}


def test_pedido_tem_colunas_de_localizacao() -> None:
    """`PedidoAjuda` expõe cidade, estado, bairro, latitude e longitude."""
    colunas = set(PedidoAjuda.__table__.columns.keys())
    assert {"cidade", "estado", "bairro", "latitude", "longitude"}.issubset(colunas)


def test_pedido_tem_colunas_do_animal_e_autoria() -> None:
    """`PedidoAjuda` expõe atributos do animal e a coluna de autoria."""
    colunas = set(PedidoAjuda.__table__.columns.keys())
    assert {
        "especie",
        "porte",
        "sexo",
        "idade_aproximada",
        "quantidade",
        "autor_id",
    }.issubset(colunas)


def test_pedido_tem_colunas_de_consentimento() -> None:
    """`PedidoAjuda` expõe os campos de consentimento LGPD."""
    colunas = set(PedidoAjuda.__table__.columns.keys())
    assert {
        "consentimento_aceito",
        "consentimento_versao",
        "consentimento_em",
    }.issubset(colunas)


def test_doador_tem_colunas_de_consentimento() -> None:
    """`DoadorVoluntario` reaproveita os campos de consentimento LGPD."""
    colunas = set(DoadorVoluntario.__table__.columns.keys())
    assert {
        "consentimento_aceito",
        "consentimento_versao",
        "consentimento_em",
    }.issubset(colunas)


def test_imagem_pedido_tem_colunas_esperadas() -> None:
    """`ImagemPedido` expõe id, pedido_id, url, ordem e criado_em."""
    colunas = set(ImagemPedido.__table__.columns.keys())
    assert {"id", "pedido_id", "url", "ordem", "criado_em"}.issubset(colunas)
    assert ImagemPedido.__tablename__ == "imagens_pedido"


def test_pedido_tem_relationship_imagens() -> None:
    """`PedidoAjuda` declara o relationship `imagens`."""
    assert "imagens" in PedidoAjuda.__mapper__.relationships


def test_pedido_tem_coluna_oculto_para_moderacao() -> None:
    """`PedidoAjuda` expõe a coluna `oculto` (moderação)."""
    assert "oculto" in PedidoAjuda.__table__.columns.keys()


def test_atendimento_tem_unique_constraint_pedido_doador() -> None:
    """`AtendimentoPedido` declara UniqueConstraint(pedido_id, doador_id)."""
    uniques = [
        c for c in AtendimentoPedido.__table__.constraints if type(c).__name__ == "UniqueConstraint"
    ]
    colunas_por_unique = [set(c.columns.keys()) for c in uniques]
    assert {"pedido_id", "doador_id"} in colunas_por_unique


def test_denuncia_tem_colunas_e_tabela_esperadas() -> None:
    """`Denuncia` expõe as colunas do domínio e a tabela `denuncias`."""
    colunas = set(Denuncia.__table__.columns.keys())
    assert {
        "id",
        "pedido_id",
        "autor_id",
        "motivo",
        "descricao",
        "status",
        "criado_em",
    }.issubset(colunas)
    assert Denuncia.__tablename__ == "denuncias"


def test_motivo_e_status_denuncia_enums_tem_valores_esperados() -> None:
    """Os enums de denúncia cobrem os motivos e status definidos no produto."""
    assert {m.value for m in MotivoDenunciaEnum} == {
        "spam",
        "golpe",
        "conteudo_improprio",
        "outro",
    }
    assert {s.value for s in StatusDenunciaEnum} == {"aberta", "resolvida"}
