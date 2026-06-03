"""Contexto de requisição (request-id) compartilhado entre middleware, logging e erros.

Mantém o `request_id` da requisição corrente em um `ContextVar`, permitindo que o
formatter de logging e os handlers de erro recuperem o identificador sem precisar
recebê-lo explicitamente em cada chamada.
"""

from __future__ import annotations

from contextvars import ContextVar

#: Identificador da requisição corrente; vazio fora de um ciclo de request.
_request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def definir_request_id(request_id: str) -> None:
    """Define o request-id da requisição corrente.

    Args:
        request_id: identificador único da requisição.

    Side Effects:
        Atualiza o `ContextVar` do contexto de execução atual.
    """
    _request_id_var.set(request_id)


def obter_request_id() -> str:
    """Retorna o request-id da requisição corrente.

    Returns:
        O identificador da requisição, ou string vazia se não houver requisição
        em andamento no contexto atual.
    """
    return _request_id_var.get()
