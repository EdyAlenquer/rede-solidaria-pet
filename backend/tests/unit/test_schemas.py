"""Testes de validação dos schemas Pydantic."""

import pytest
from pydantic import ValidationError

from app.models.enums import StatusPedidoEnum, UrgenciaEnum
from app.schemas import (
    AtendimentoCreate,
    DoadorCreate,
    PedidoCreate,
    PedidoStatusUpdate,
    PedidoUpdate,
)


def test_pedido_create_aceita_payload_valido() -> None:
    """PedidoCreate aceita um payload com todos os campos obrigatórios."""
    p = PedidoCreate(
        titulo="Cãozinho ferido",
        descricao="Encontrado na rua X, precisa de atendimento veterinário.",
        categoria="resgate",
        urgencia=UrgenciaEnum.ALTA,
        contato="11999990000",
    )
    assert p.urgencia is UrgenciaEnum.ALTA


def test_pedido_create_rejeita_titulo_curto() -> None:
    """`titulo` com menos de 3 caracteres deve falhar."""
    with pytest.raises(ValidationError):
        PedidoCreate(
            titulo="X",
            descricao="Descrição válida com texto suficiente.",
            categoria="resgate",
            urgencia=UrgenciaEnum.BAIXA,
            contato="11999990000",
        )


def test_pedido_update_permite_payload_vazio() -> None:
    """PedidoUpdate aceita objeto sem campos (atualização nula é permitida)."""
    u = PedidoUpdate()
    assert u.model_dump(exclude_unset=True) == {}


def test_pedido_status_update_exige_status_valido() -> None:
    """PedidoStatusUpdate aceita apenas valores do enum."""
    ok = PedidoStatusUpdate(status=StatusPedidoEnum.EM_ANDAMENTO)
    assert ok.status is StatusPedidoEnum.EM_ANDAMENTO

    with pytest.raises(ValidationError):
        PedidoStatusUpdate(status="invalido")  # type: ignore[arg-type]


def test_doador_create_exige_telefone_ou_email() -> None:
    """DoadorCreate falha quando nenhum contato é informado."""
    with pytest.raises(ValidationError):
        DoadorCreate(nome="Sem Contato")


def test_doador_create_aceita_apenas_telefone() -> None:
    """DoadorCreate aceita doador com apenas telefone."""
    d = DoadorCreate(nome="Maria", telefone="11988887777")
    assert d.telefone == "11988887777"
    assert d.email is None


def test_doador_create_aceita_apenas_email_valido() -> None:
    """DoadorCreate aceita doador com apenas e-mail válido."""
    d = DoadorCreate(nome="João", email="joao@example.com")
    assert d.email == "joao@example.com"


def test_doador_create_rejeita_email_invalido() -> None:
    """E-mail mal formado é rejeitado pelo EmailStr."""
    with pytest.raises(ValidationError):
        DoadorCreate(nome="X", email="nao-eh-email")


def test_atendimento_create_exige_doador_id_positivo() -> None:
    """AtendimentoCreate rejeita `doador_id` <= 0."""
    with pytest.raises(ValidationError):
        AtendimentoCreate(doador_id=0, tipo_ajuda="ração")


def test_atendimento_create_aceita_payload_valido() -> None:
    """AtendimentoCreate aceita payload mínimo com tipo_ajuda e doador_id."""
    a = AtendimentoCreate(doador_id=1, tipo_ajuda="ração")
    assert a.tipo_ajuda == "ração"
    assert a.observacao is None
