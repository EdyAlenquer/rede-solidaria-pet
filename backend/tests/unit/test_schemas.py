"""Testes de validação dos schemas Pydantic."""

import pytest
from pydantic import ValidationError

from app.models.enums import EspecieEnum, PorteEnum, SexoEnum, StatusPedidoEnum, UrgenciaEnum
from app.schemas import (
    AtendimentoCreate,
    DoadorCreate,
    PedidoCreate,
    PedidoStatusUpdate,
    PedidoUpdate,
)

_PEDIDO_VALIDO = {
    "titulo": "Cãozinho ferido",
    "descricao": "Encontrado na rua X, precisa de atendimento veterinário.",
    "categoria": "resgate",
    "urgencia": UrgenciaEnum.ALTA,
    "contato": "11999990000",
    "cidade": "São Paulo",
    "estado": "SP",
    "consentimento_aceito": True,
}


def test_pedido_create_aceita_payload_valido() -> None:
    """PedidoCreate aceita um payload com todos os campos obrigatórios."""
    p = PedidoCreate(**_PEDIDO_VALIDO)
    assert p.urgencia is UrgenciaEnum.ALTA
    assert p.cidade == "São Paulo"
    assert p.estado == "SP"
    assert p.consentimento_aceito is True


def test_pedido_create_rejeita_titulo_curto() -> None:
    """`titulo` com menos de 3 caracteres deve falhar."""
    with pytest.raises(ValidationError):
        PedidoCreate(**{**_PEDIDO_VALIDO, "titulo": "X"})


def test_pedido_create_exige_cidade_e_estado() -> None:
    """PedidoCreate falha sem cidade e/ou estado."""
    sem_cidade = {k: v for k, v in _PEDIDO_VALIDO.items() if k != "cidade"}
    sem_estado = {k: v for k, v in _PEDIDO_VALIDO.items() if k != "estado"}
    with pytest.raises(ValidationError):
        PedidoCreate(**sem_cidade)
    with pytest.raises(ValidationError):
        PedidoCreate(**sem_estado)


def test_pedido_create_normaliza_e_valida_uf() -> None:
    """`estado` é normalizado para 2 letras maiúsculas; valores inválidos falham."""
    p = PedidoCreate(**{**_PEDIDO_VALIDO, "estado": "sp"})
    assert p.estado == "SP"

    with pytest.raises(ValidationError):
        PedidoCreate(**{**_PEDIDO_VALIDO, "estado": "São Paulo"})
    with pytest.raises(ValidationError):
        PedidoCreate(**{**_PEDIDO_VALIDO, "estado": "S"})


def test_pedido_create_aceita_atributos_do_animal_opcionais() -> None:
    """Atributos do animal são opcionais e tipados pelos enums."""
    p = PedidoCreate(
        **{
            **_PEDIDO_VALIDO,
            "especie": "cao",
            "porte": "medio",
            "sexo": "macho",
            "idade_aproximada": "2 anos",
            "quantidade": 3,
            "bairro": "Centro",
            "latitude": -23.55,
            "longitude": -46.63,
        }
    )
    assert p.especie is EspecieEnum.CAO
    assert p.porte is PorteEnum.MEDIO
    assert p.sexo is SexoEnum.MACHO
    assert p.quantidade == 3


def test_pedido_create_rejeita_quantidade_menor_que_um() -> None:
    """`quantidade` deve ser >= 1."""
    with pytest.raises(ValidationError):
        PedidoCreate(**{**_PEDIDO_VALIDO, "quantidade": 0})


def test_pedido_create_exige_consentimento_aceito_true() -> None:
    """PedidoCreate rejeita consentimento_aceito=False com mensagem PT-BR."""
    with pytest.raises(ValidationError) as exc:
        PedidoCreate(**{**_PEDIDO_VALIDO, "consentimento_aceito": False})
    assert "consentimento" in str(exc.value).lower()


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
        DoadorCreate(nome="Sem Contato", consentimento_aceito=True)


def test_doador_create_aceita_apenas_telefone() -> None:
    """DoadorCreate aceita doador com apenas telefone."""
    d = DoadorCreate(nome="Maria", telefone="11988887777", consentimento_aceito=True)
    assert d.telefone == "11988887777"
    assert d.email is None


def test_doador_create_aceita_apenas_email_valido() -> None:
    """DoadorCreate aceita doador com apenas e-mail válido."""
    d = DoadorCreate(nome="João", email="joao@example.com", consentimento_aceito=True)
    assert d.email == "joao@example.com"


def test_doador_create_rejeita_email_invalido() -> None:
    """E-mail mal formado é rejeitado pelo EmailStr."""
    with pytest.raises(ValidationError):
        DoadorCreate(nome="X", email="nao-eh-email", consentimento_aceito=True)


def test_doador_create_exige_consentimento_aceito_true() -> None:
    """DoadorCreate rejeita consentimento_aceito=False com mensagem PT-BR."""
    with pytest.raises(ValidationError) as exc:
        DoadorCreate(nome="Maria", telefone="11988887777", consentimento_aceito=False)
    assert "consentimento" in str(exc.value).lower()


def test_atendimento_create_nao_aceita_doador_id_no_corpo() -> None:
    """AtendimentoCreate ignora `doador_id` no corpo (derivado do usuário atual)."""
    a = AtendimentoCreate(doador_id=1, tipo_ajuda="ração")
    assert not hasattr(a, "doador_id")


def test_atendimento_create_aceita_payload_valido() -> None:
    """AtendimentoCreate aceita payload mínimo com apenas tipo_ajuda."""
    a = AtendimentoCreate(tipo_ajuda="ração")
    assert a.tipo_ajuda == "ração"
    assert a.observacao is None


def test_imagem_read_expoe_id_url_e_ordem() -> None:
    """ImagemRead expõe os campos públicos da imagem."""
    from app.schemas import ImagemRead

    img = ImagemRead(id=1, url="https://cdn/x.jpg", ordem=2)
    assert img.id == 1
    assert img.url == "https://cdn/x.jpg"
    assert img.ordem == 2


def test_pedido_read_inclui_imagens_default_vazia() -> None:
    """PedidoRead expõe `imagens` com default lista vazia."""
    from app.schemas import PedidoRead

    pedido = PedidoRead(
        id=1,
        titulo="Cãozinho ferido",
        descricao="Encontrado na rua X, precisa de atendimento veterinário.",
        categoria="resgate",
        urgencia=UrgenciaEnum.ALTA,
        cidade="São Paulo",
        estado="SP",
        consentimento_aceito=True,
        status=StatusPedidoEnum.ABERTO,
        oculto=False,
        data_criacao="2026-06-01T00:00:00+00:00",
    )
    assert pedido.imagens == []
    assert "contato" not in pedido.model_dump()
