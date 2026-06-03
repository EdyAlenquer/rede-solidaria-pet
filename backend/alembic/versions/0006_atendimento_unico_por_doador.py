"""atendimento unico por doador e pedido

Fase B2 — impõe que um doador registre no máximo um atendimento por pedido,
via ``UniqueConstraint(pedido_id, doador_id)`` na tabela ``atendimentos``.

A constraint é criada com ``batch_alter_table`` para compatibilidade com o
SQLite, que não suporta ``ALTER TABLE ... ADD CONSTRAINT``.

Revision ID: 0006_atendimento_unico_por_doador
Revises: 0005_autenticacao_usuarios
Create Date: 2026-06-02 22:10:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0006_atendimento_unico_por_doador"
down_revision: str | None = "0005_autenticacao_usuarios"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_UQ_ATENDIMENTOS = "uq_atendimentos_pedido_doador"


def upgrade() -> None:
    """Cria a UniqueConstraint ``(pedido_id, doador_id)`` em ``atendimentos``."""
    with op.batch_alter_table("atendimentos", schema=None) as batch_op:
        batch_op.create_unique_constraint(_UQ_ATENDIMENTOS, ["pedido_id", "doador_id"])


def downgrade() -> None:
    """Remove a UniqueConstraint ``(pedido_id, doador_id)`` de ``atendimentos``."""
    with op.batch_alter_table("atendimentos", schema=None) as batch_op:
        batch_op.drop_constraint(_UQ_ATENDIMENTOS, type_="unique")
