"""moderacao: coluna oculto em pedidos e tabela denuncias

Fase B2 — adiciona a moderação de conteúdo:

- ``pedidos.oculto`` (Boolean NOT NULL default False, indexado): pedidos
  ocultos não aparecem nas leituras públicas.
- Nova tabela ``denuncias`` (id, pedido_id FK CASCADE, autor_id FK usuarios
  nullable ON DELETE SET NULL, motivo ENUM ``motivo_denuncia_enum``, descricao
  Text nullable, status ENUM ``status_denuncia_enum`` default ``ABERTA``,
  criado_em timestamp).

A coluna em ``pedidos`` é adicionada via ``batch_alter_table`` para
compatibilidade com o SQLite.

Revision ID: 0007_moderacao_denuncias
Revises: 0006_atend_unico_doador
Create Date: 2026-06-02 22:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007_moderacao_denuncias"
down_revision: str | None = "0006_atend_unico_doador"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Adiciona ``pedidos.oculto`` e cria a tabela ``denuncias``."""
    with op.batch_alter_table("pedidos", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "oculto",
                sa.Boolean(),
                server_default=sa.false(),
                nullable=False,
            )
        )
        batch_op.create_index(batch_op.f("ix_pedidos_oculto"), ["oculto"], unique=False)

    op.create_table(
        "denuncias",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("pedido_id", sa.Integer(), nullable=False),
        sa.Column("autor_id", sa.Integer(), nullable=True),
        sa.Column(
            "motivo",
            sa.Enum(
                "SPAM",
                "GOLPE",
                "CONTEUDO_IMPROPRIO",
                "OUTRO",
                name="motivo_denuncia_enum",
            ),
            nullable=False,
        ),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("ABERTA", "RESOLVIDA", name="status_denuncia_enum"),
            server_default="ABERTA",
            nullable=False,
        ),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["pedido_id"], ["pedidos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["autor_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("denuncias", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_denuncias_pedido_id"), ["pedido_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_denuncias_autor_id"), ["autor_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_denuncias_status"), ["status"], unique=False)


def downgrade() -> None:
    """Remove a tabela ``denuncias`` e a coluna ``pedidos.oculto``."""
    with op.batch_alter_table("denuncias", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_denuncias_status"))
        batch_op.drop_index(batch_op.f("ix_denuncias_autor_id"))
        batch_op.drop_index(batch_op.f("ix_denuncias_pedido_id"))
    op.drop_table("denuncias")

    with op.batch_alter_table("pedidos", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_pedidos_oculto"))
        batch_op.drop_column("oculto")
