"""Testes do UsuarioRepository e UsuarioService."""

import pytest
from sqlalchemy.orm import Session

from app.core.errors import EmailJaCadastradoError, UsuarioNotFoundError
from app.core.security import verificar_senha
from app.models.enums import PapelUsuarioEnum
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas import UsuarioCreate
from app.services.usuario_service import UsuarioService


def _payload(**overrides) -> UsuarioCreate:
    """Constrói um UsuarioCreate válido com overrides opcionais."""
    base = {
        "nome": "Ana Protetora",
        "email": "ana@example.com",
        "senha": "senha-com-8+",
        "consentimento_aceito": True,
    }
    base.update(overrides)
    return UsuarioCreate(**base)


def _service(db_session: Session) -> UsuarioService:
    """Constrói um UsuarioService ligado à sessão de teste."""
    return UsuarioService(UsuarioRepository(db_session))


def test_create_persiste_usuario_com_senha_hasheada(db_session: Session) -> None:
    """`create` salva o usuário com a senha hasheada (nunca em texto puro)."""
    service = _service(db_session)

    usuario = service.create(_payload())

    assert usuario.id is not None
    assert usuario.papel is PapelUsuarioEnum.PROTETOR
    assert usuario.senha_hash != "senha-com-8+"
    assert verificar_senha("senha-com-8+", usuario.senha_hash)


def test_create_email_duplicado_levanta_erro(db_session: Session) -> None:
    """Registrar dois usuários com o mesmo email levanta `EmailJaCadastradoError`."""
    service = _service(db_session)
    service.create(_payload(email="dup@example.com"))

    with pytest.raises(EmailJaCadastradoError):
        service.create(_payload(nome="Outro", email="dup@example.com"))


def test_autenticar_retorna_usuario_com_credenciais_corretas(db_session: Session) -> None:
    """`autenticar` retorna o usuário quando email e senha conferem."""
    service = _service(db_session)
    criado = service.create(_payload(email="login@example.com", senha="minha-senha-1"))

    autenticado = service.autenticar("login@example.com", "minha-senha-1")

    assert autenticado is not None
    assert autenticado.id == criado.id


def test_autenticar_retorna_none_com_senha_errada(db_session: Session) -> None:
    """`autenticar` retorna None quando a senha está errada."""
    service = _service(db_session)
    service.create(_payload(email="login@example.com", senha="minha-senha-1"))

    assert service.autenticar("login@example.com", "senha-errada") is None


def test_autenticar_retorna_none_para_email_inexistente(db_session: Session) -> None:
    """`autenticar` retorna None quando o email não existe."""
    service = _service(db_session)

    assert service.autenticar("ninguem@example.com", "qualquer") is None


def test_get_by_id_levanta_not_found(db_session: Session) -> None:
    """`get_by_id` levanta `UsuarioNotFoundError` quando o id não existe."""
    service = _service(db_session)

    with pytest.raises(UsuarioNotFoundError):
        service.get_by_id(9999)


def test_get_by_email_retorna_usuario(db_session: Session) -> None:
    """`get_by_email` no repositório encontra o usuário pelo email."""
    repo = UsuarioRepository(db_session)
    UsuarioService(repo).create(_payload(email="busca@example.com"))

    encontrado = repo.get_by_email("busca@example.com")

    assert encontrado is not None
    assert encontrado.email == "busca@example.com"


def test_get_by_id_ignora_soft_deletado(db_session: Session) -> None:
    """Usuário soft-deletado não é retornado por `get_by_id` do repositório."""
    from sqlalchemy import func

    repo = UsuarioRepository(db_session)
    usuario = UsuarioService(repo).create(_payload(email="morto@example.com"))
    usuario.deleted_at = func.now()
    db_session.commit()

    assert repo.get_by_id(usuario.id) is None


def test_anonimizar_aplica_dados_anonimos_e_soft_delete(db_session: Session) -> None:
    """`anonimizar` substitui nome/email/telefone, invalida senha e marca soft-delete."""
    service = _service(db_session)
    usuario = service.create(
        _payload(email="vivo@example.com", telefone="11999998888", senha="minha-senha-1")
    )
    senha_hash_original = usuario.senha_hash

    service.anonimizar(usuario.id)

    db_session.expire_all()
    bruto = db_session.get(type(usuario), usuario.id)
    assert bruto.deleted_at is not None
    assert bruto.nome == "Usuário removido"
    assert bruto.email == f"removido+{usuario.id}@anonimizado.local"
    assert bruto.telefone is None
    assert bruto.senha_hash != senha_hash_original
    assert not verificar_senha("minha-senha-1", bruto.senha_hash)


def test_anonimizar_usuario_inexistente_levanta_not_found(db_session: Session) -> None:
    """`anonimizar` levanta `UsuarioNotFoundError` quando o id não existe."""
    service = _service(db_session)

    with pytest.raises(UsuarioNotFoundError):
        service.anonimizar(9999)
