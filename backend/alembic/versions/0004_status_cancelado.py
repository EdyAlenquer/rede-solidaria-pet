"""status cancelado

Fase A3 — adiciona o valor ``CANCELADO`` ao enum de status do pedido
(``status_pedido_enum``), necessário para a máquina de estados explícita do
``PedidoService`` (ABERTO/EM_ANDAMENTO/CONCLUIDO/CANCELADO).

Comportamento por banco:

- **PostgreSQL**: o status é um tipo ENUM nativo; o novo valor é adicionado com
  ``ALTER TYPE ... ADD VALUE IF NOT EXISTS 'CANCELADO'``. Essa operação é
  irreversível no Postgres (não há ``DROP VALUE``), então o ``downgrade`` é um
  no-op explícito para esse backend.
- **SQLite**: o enum é mapeado para ``VARCHAR`` sem CHECK constraint, então não
  há alteração de schema a aplicar — o upgrade e o downgrade são no-ops.

Revision ID: 0004_status_cancelado
Revises: 0003_produto_imagens
Create Date: 2026-06-02 10:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004_status_cancelado"
down_revision: str | None = "0003_produto_imagens"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Adiciona o valor ``CANCELADO`` ao enum de status no Postgres.

    Em SQLite é no-op, pois o enum é armazenado como ``VARCHAR`` sem CHECK.

    Side Effects:
        No Postgres, executa ``ALTER TYPE status_pedido_enum ADD VALUE`` fora de
        transação (exigência do Postgres para alteração de tipos ENUM).
    """
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        # ALTER TYPE ... ADD VALUE não pode rodar dentro de um bloco de
        # transação no Postgres; emite-se em autocommit.
        with op.get_context().autocommit_block():
            op.execute("ALTER TYPE status_pedido_enum ADD VALUE IF NOT EXISTS 'CANCELADO'")


def downgrade() -> None:
    """Reverte a adição do valor ``CANCELADO`` (no-op).

    O PostgreSQL não suporta remover valores de um tipo ENUM, e no SQLite não há
    schema a reverter. Portanto, o downgrade é intencionalmente um no-op.
    """
