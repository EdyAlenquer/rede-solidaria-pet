"""Testes do DoadorRepository."""

from sqlalchemy.orm import Session

from app.repositories.doador_repository import DoadorRepository
from app.schemas import DoadorCreate, DoadorUpdate


def test_create_persiste_doador_com_id(db_session: Session) -> None:
    """`create` retorna doador com `id` preenchido."""
    repo = DoadorRepository(db_session)
    doador = repo.create(
        DoadorCreate(nome="Maria", telefone="11999990000", consentimento_aceito=True)
    )

    assert doador.id is not None
    assert doador.nome == "Maria"


def test_get_by_id_retorna_doador_existente(db_session: Session) -> None:
    """`get_by_id` retorna o doador criado."""
    repo = DoadorRepository(db_session)
    criado = repo.create(
        DoadorCreate(nome="João", email="joao@example.com", consentimento_aceito=True)
    )

    encontrado = repo.get_by_id(criado.id)

    assert encontrado is not None
    assert encontrado.email == "joao@example.com"


def test_get_by_id_retorna_none_para_inexistente(db_session: Session) -> None:
    """`get_by_id` retorna None para id inexistente."""
    repo = DoadorRepository(db_session)
    assert repo.get_by_id(9999) is None


def test_update_aplica_apenas_campos_informados(db_session: Session) -> None:
    """`update` modifica somente os campos definidos."""
    repo = DoadorRepository(db_session)
    doador = repo.create(
        DoadorCreate(nome="Original", telefone="11999990000", consentimento_aceito=True)
    )

    atualizado = repo.update(doador.id, DoadorUpdate(nome="Novo Nome"))

    assert atualizado is not None
    assert atualizado.nome == "Novo Nome"
    assert atualizado.telefone == "11999990000"


def test_update_retorna_none_para_inexistente(db_session: Session) -> None:
    """`update` retorna None se o doador não existir."""
    repo = DoadorRepository(db_session)
    assert repo.update(9999, DoadorUpdate(nome="Qualquer")) is None


def test_anonimizar_por_email_zera_pii(db_session: Session) -> None:
    """`anonimizar_por_email` zera nome/email/telefone e marca soft-delete."""
    repo = DoadorRepository(db_session)
    doador = repo.create(
        DoadorCreate(
            nome="Maria PII",
            email="maria@example.com",
            telefone="11999990000",
            consentimento_aceito=True,
        )
    )

    afetou = repo.anonimizar_por_email("maria@example.com")

    assert afetou is True
    db_session.expire_all()
    bruto = repo.get_by_id(doador.id)
    assert bruto.nome == "Doador removido"
    assert bruto.email == f"removido+doador{doador.id}@anonimizado.local"
    assert bruto.telefone is None
    assert bruto.deleted_at is not None


def test_anonimizar_por_email_inexistente_retorna_false(db_session: Session) -> None:
    """`anonimizar_por_email` retorna False quando não há doador com o e-mail."""
    repo = DoadorRepository(db_session)
    assert repo.anonimizar_por_email("ninguem@example.com") is False
