"""autenticacao: usuarios e fk de autoria

Fase B1 — cria a tabela ``usuarios`` (contas autenticáveis de protetor/admin)
e promove ``pedidos.autor_id`` a chave estrangeira real para ``usuarios.id``.

- Nova tabela ``usuarios`` (id, nome, email único + indexado, senha_hash,
  papel ENUM ``papel_usuario_enum`` default ``PROTETOR``, telefone, campos de
  consentimento LGPD e timestamps com soft-delete).
- ``pedidos.autor_id`` continua NULLABLE (pedidos antigos podem não ter autor),
  mas passa a ter FK para ``usuarios.id`` com ``ON DELETE SET NULL`` — quando um
  usuário é removido, os pedidos órfãos preservam o histórico sem autor.

A FK em ``pedidos`` é criada via ``batch_alter_table`` para compatibilidade com
o SQLite, que não suporta ``ALTER TABLE ... ADD CONSTRAINT``.

Revision ID: 0005_autenticacao_usuarios
Revises: 0004_status_cancelado
Create Date: 2026-06-02 21:39:23.952346

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005_autenticacao_usuarios"
down_revision: str | None = "0004_status_cancelado"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_FK_PEDIDOS_AUTOR = "fk_pedidos_autor_id_usuarios"


def upgrade() -> None:
    """Cria ``usuarios`` e a FK ``pedidos.autor_id -> usuarios.id``."""
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=120), nullable=False),
        sa.Column("senha_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "papel",
            sa.Enum("PROTETOR", "ADMIN", name="papel_usuario_enum"),
            server_default="PROTETOR",
            nullable=False,
        ),
        sa.Column("telefone", sa.String(length=40), nullable=True),
        sa.Column(
            "consentimento_aceito",
            sa.Boolean(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("consentimento_versao", sa.String(length=20), nullable=True),
        sa.Column("consentimento_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_usuarios_email"),
    )
    with op.batch_alter_table("usuarios", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_usuarios_email"), ["email"], unique=False)

    with op.batch_alter_table("pedidos", schema=None) as batch_op:
        batch_op.create_foreign_key(
            _FK_PEDIDOS_AUTOR,
            "usuarios",
            ["autor_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    """Remove a FK de autoria e descarta a tabela ``usuarios``."""
    with op.batch_alter_table("pedidos", schema=None) as batch_op:
        batch_op.drop_constraint(_FK_PEDIDOS_AUTOR, type_="foreignkey")

    with op.batch_alter_table("usuarios", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_usuarios_email"))

    op.drop_table("usuarios")
