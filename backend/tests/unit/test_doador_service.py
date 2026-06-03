"""Testes do DoadorService (regras de negócio sobre DoadorRepository)."""

import pytest
from sqlalchemy.orm import Session

from app.core.errors import DoadorNotFoundError
from app.repositories.doador_repository import DoadorRepository
from app.schemas import DoadorCreate
from app.services import DoadorService


def test_doador_service_eh_exportado_pelo_pacote_de_servicos() -> None:
    """`DoadorService` está disponível pelo pacote público de serviços."""
    assert DoadorService.__name__ == "DoadorService"


def test_create_persiste_doador(db_session: Session) -> None:
    """`create` persiste o doador e retorna o registro com id."""
    service = DoadorService(DoadorRepository(db_session))

    doador = service.create(
        DoadorCreate(nome="Maria", telefone="11999990000", consentimento_aceito=True)
    )

    assert doador.id is not None
    assert doador.nome == "Maria"


def test_get_by_id_retorna_doador_existente(db_session: Session) -> None:
    """`get_by_id` retorna o doador quando o id existe."""
    service = DoadorService(DoadorRepository(db_session))
    criado = service.create(
        DoadorCreate(nome="João", email="joao@example.com", consentimento_aceito=True)
    )

    encontrado = service.get_by_id(criado.id)

    assert encontrado.email == "joao@example.com"


def test_get_by_id_lanca_404_para_inexistente(db_session: Session) -> None:
    """`get_by_id` levanta `DoadorNotFoundError` quando o id não existe."""
    service = DoadorService(DoadorRepository(db_session))

    with pytest.raises(DoadorNotFoundError):
        service.get_by_id(9999)
