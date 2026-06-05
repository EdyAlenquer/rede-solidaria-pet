"""campos de produto e imagens

Fase A2 — evolui `PedidoAjuda` para suportar as features de produto e cria a
tabela `imagens_pedido`:

- Localização em `pedidos`: `cidade` (NOT NULL), `estado` (UF NOT NULL),
  `bairro`, `latitude`, `longitude`.
- Atributos do animal (opcionais): `especie`, `porte`, `sexo`,
  `idade_aproximada`, `quantidade` (NOT NULL, default 1, >= 1).
- Autoria: `autor_id` (Integer NULLABLE, indexado, SEM constraint de FK por
  enquanto — virará FK para `usuarios.id` na milestone de autenticação).
- Consentimento LGPD em `pedidos` e `doadores`: `consentimento_aceito`
  (NOT NULL default False), `consentimento_versao`, `consentimento_em`.
- Nova tabela `imagens_pedido` (id, pedido_id FK CASCADE, url, ordem,
  criado_em) com índice em `pedido_id`.

Backfill seguro de colunas NOT NULL: como já podem existir pedidos antigos sem
localização, `cidade`/`estado` entram com `server_default=""` e `quantidade`
com `server_default="1"`. Esses defaults de servidor são então removidos com
`alter_column`, deixando a coluna NOT NULL sem default no schema final — que é
exatamente o estado dos modelos ORM. O upgrade é, assim, idempotente em bancos
populados e em bancos vazios.

Revision ID: 0003_produto_imagens
Revises: affcf1b343bb
Create Date: 2026-06-02 07:45:32.901954

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003_produto_imagens"
down_revision: str | None = "affcf1b343bb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_especie_enum = sa.Enum("CAO", "GATO", "OUTRO", name="especie_enum")
_porte_enum = sa.Enum("PEQUENO", "MEDIO", "GRANDE", name="porte_enum")
_sexo_enum = sa.Enum("MACHO", "FEMEA", "DESCONHECIDO", name="sexo_enum")


def upgrade() -> None:
    """Aplica os novos campos de produto e cria `imagens_pedido`."""
    op.create_table(
        "imagens_pedido",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("pedido_id", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("ordem", sa.Integer(), nullable=False),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["pedido_id"], ["pedidos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("imagens_pedido", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_imagens_pedido_pedido_id"), ["pedido_id"], unique=False
        )

    with op.batch_alter_table("doadores", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "consentimento_aceito",
                sa.Boolean(),
                server_default=sa.text("0"),
                nullable=False,
            )
        )
        batch_op.add_column(sa.Column("consentimento_versao", sa.String(length=20), nullable=True))
        batch_op.add_column(
            sa.Column("consentimento_em", sa.DateTime(timezone=True), nullable=True)
        )

    with op.batch_alter_table("pedidos", schema=None) as batch_op:
        # Localização — backfill seguro para linhas pré-existentes.
        batch_op.add_column(
            sa.Column("cidade", sa.String(length=80), nullable=False, server_default="")
        )
        batch_op.add_column(
            sa.Column("estado", sa.String(length=2), nullable=False, server_default="")
        )
        batch_op.add_column(sa.Column("bairro", sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column("latitude", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("longitude", sa.Float(), nullable=True))
        # Atributos do animal (opcionais).
        batch_op.add_column(sa.Column("especie", _especie_enum, nullable=True))
        batch_op.add_column(sa.Column("porte", _porte_enum, nullable=True))
        batch_op.add_column(sa.Column("sexo", _sexo_enum, nullable=True))
        batch_op.add_column(sa.Column("idade_aproximada", sa.String(length=40), nullable=True))
        batch_op.add_column(
            sa.Column("quantidade", sa.Integer(), nullable=False, server_default="1")
        )
        # Autoria — coluna simples, sem FK por enquanto.
        batch_op.add_column(sa.Column("autor_id", sa.Integer(), nullable=True))
        # Consentimento LGPD.
        batch_op.add_column(
            sa.Column(
                "consentimento_aceito",
                sa.Boolean(),
                server_default=sa.text("0"),
                nullable=False,
            )
        )
        batch_op.add_column(sa.Column("consentimento_versao", sa.String(length=20), nullable=True))
        batch_op.add_column(
            sa.Column("consentimento_em", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.create_index(batch_op.f("ix_pedidos_autor_id"), ["autor_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_pedidos_cidade"), ["cidade"], unique=False)
        batch_op.create_index(batch_op.f("ix_pedidos_estado"), ["estado"], unique=False)
        batch_op.create_index(batch_op.f("ix_pedidos_especie"), ["especie"], unique=False)
        batch_op.create_index(batch_op.f("ix_pedidos_porte"), ["porte"], unique=False)

    # Remove os server_defaults de backfill: o schema final dos modelos ORM
    # tem essas colunas NOT NULL sem default de servidor.
    with op.batch_alter_table("pedidos", schema=None) as batch_op:
        batch_op.alter_column("cidade", server_default=None)
        batch_op.alter_column("estado", server_default=None)
        batch_op.alter_column("quantidade", server_default=None)


def downgrade() -> None:
    """Reverte os campos de produto e remove `imagens_pedido`."""
    with op.batch_alter_table("pedidos", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_pedidos_porte"))
        batch_op.drop_index(batch_op.f("ix_pedidos_especie"))
        batch_op.drop_index(batch_op.f("ix_pedidos_estado"))
        batch_op.drop_index(batch_op.f("ix_pedidos_cidade"))
        batch_op.drop_index(batch_op.f("ix_pedidos_autor_id"))
        batch_op.drop_column("consentimento_em")
        batch_op.drop_column("consentimento_versao")
        batch_op.drop_column("consentimento_aceito")
        batch_op.drop_column("autor_id")
        batch_op.drop_column("quantidade")
        batch_op.drop_column("idade_aproximada")
        batch_op.drop_column("sexo")
        batch_op.drop_column("porte")
        batch_op.drop_column("especie")
        batch_op.drop_column("longitude")
        batch_op.drop_column("latitude")
        batch_op.drop_column("bairro")
        batch_op.drop_column("estado")
        batch_op.drop_column("cidade")

    with op.batch_alter_table("doadores", schema=None) as batch_op:
        batch_op.drop_column("consentimento_em")
        batch_op.drop_column("consentimento_versao")
        batch_op.drop_column("consentimento_aceito")

    with op.batch_alter_table("imagens_pedido", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_imagens_pedido_pedido_id"))
    op.drop_table("imagens_pedido")
