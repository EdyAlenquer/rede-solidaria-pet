"""Testes do ImagemService (regras de upload/remoção de imagens de pedido)."""

import pytest
from sqlalchemy.orm import Session

from app.config import Settings
from app.core.errors import (
    AcessoNegadoError,
    ImagemMuitoGrandeError,
    ImagemNotFoundError,
    LimiteImagensExcedidoError,
    PedidoNotFoundError,
    TipoImagemInvalidoError,
)
from app.core.storage import StorageBackend
from app.models.enums import CategoriaEnum, PapelUsuarioEnum, UrgenciaEnum
from app.models.pedido import PedidoAjuda
from app.models.usuario import Usuario
from app.repositories.imagem_repository import ImagemRepository
from app.repositories.pedido_repository import PedidoRepository
from app.services.imagem_service import ImagemService


class _FakeStorage(StorageBackend):
    """Storage em memória que registra salvamentos e remoções para asserts."""

    def __init__(self) -> None:
        self.salvos: dict[str, bytes] = {}
        self.removidos: list[str] = []

    def salvar(self, conteudo: bytes, nome_arquivo: str) -> str:
        url = f"/uploads/{nome_arquivo}"
        self.salvos[url] = conteudo
        return url

    def remover(self, url: str) -> None:
        self.removidos.append(url)
        self.salvos.pop(url, None)


def _criar_usuario(db: Session, *, email: str, papel: PapelUsuarioEnum) -> Usuario:
    usuario = Usuario(nome="U", email=email, senha_hash="x", papel=papel)
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


def _criar_pedido(db: Session, *, autor_id: int | None) -> PedidoAjuda:
    pedido = PedidoAjuda(
        titulo="Pedido",
        descricao="Descrição do pedido de teste.",
        categoria=CategoriaEnum.RESGATE,
        urgencia=UrgenciaEnum.ALTA,
        contato="11999990000",
        cidade="São Paulo",
        estado="SP",
        autor_id=autor_id,
    )
    db.add(pedido)
    db.commit()
    db.refresh(pedido)
    return pedido


@pytest.fixture
def storage() -> _FakeStorage:
    return _FakeStorage()


@pytest.fixture
def settings() -> Settings:
    return Settings(
        max_upload_bytes=100,
        max_imagens_por_pedido=2,
        allowed_image_types=frozenset({"image/jpeg", "image/png", "image/webp"}),
    )


def _service(db: Session, storage: _FakeStorage, settings: Settings) -> ImagemService:
    return ImagemService(
        ImagemRepository(db),
        PedidoRepository(db),
        storage=storage,
        settings=settings,
    )


def test_create_salva_no_storage_e_persiste_linha(
    db_session: Session, storage: _FakeStorage, settings: Settings
) -> None:
    """Upload válido grava no storage e cria a `ImagemPedido` com URL e ordem."""
    autor = _criar_usuario(db_session, email="autor@x.com", papel=PapelUsuarioEnum.PROTETOR)
    pedido = _criar_pedido(db_session, autor_id=autor.id)
    service = _service(db_session, storage, settings)

    imagem = service.create(pedido.id, b"abc", "image/jpeg", usuario=autor)

    assert imagem.ordem == 0
    assert imagem.url in storage.salvos
    assert imagem.url.endswith(".jpg")


def test_create_pedido_inexistente_levanta_not_found(
    db_session: Session, storage: _FakeStorage, settings: Settings
) -> None:
    """Upload em pedido inexistente levanta `PedidoNotFoundError`."""
    autor = _criar_usuario(db_session, email="autor@x.com", papel=PapelUsuarioEnum.PROTETOR)
    service = _service(db_session, storage, settings)

    with pytest.raises(PedidoNotFoundError):
        service.create(99999, b"abc", "image/jpeg", usuario=autor)


def test_create_nao_autor_levanta_acesso_negado(
    db_session: Session, storage: _FakeStorage, settings: Settings
) -> None:
    """Usuário que não é autor nem admin não pode subir imagem (403)."""
    autor = _criar_usuario(db_session, email="autor@x.com", papel=PapelUsuarioEnum.PROTETOR)
    outro = _criar_usuario(db_session, email="outro@x.com", papel=PapelUsuarioEnum.PROTETOR)
    pedido = _criar_pedido(db_session, autor_id=autor.id)
    service = _service(db_session, storage, settings)

    with pytest.raises(AcessoNegadoError):
        service.create(pedido.id, b"abc", "image/jpeg", usuario=outro)

    assert storage.salvos == {}  # nada gravado


def test_create_admin_pode_subir(
    db_session: Session, storage: _FakeStorage, settings: Settings
) -> None:
    """Admin pode subir imagem em pedido de outro autor."""
    autor = _criar_usuario(db_session, email="autor@x.com", papel=PapelUsuarioEnum.PROTETOR)
    admin = _criar_usuario(db_session, email="admin@x.com", papel=PapelUsuarioEnum.ADMIN)
    pedido = _criar_pedido(db_session, autor_id=autor.id)
    service = _service(db_session, storage, settings)

    imagem = service.create(pedido.id, b"abc", "image/png", usuario=admin)
    assert imagem.url.endswith(".png")


def test_create_tipo_invalido_levanta_415(
    db_session: Session, storage: _FakeStorage, settings: Settings
) -> None:
    """Content-type fora da lista permitida levanta `TipoImagemInvalidoError`."""
    autor = _criar_usuario(db_session, email="autor@x.com", papel=PapelUsuarioEnum.PROTETOR)
    pedido = _criar_pedido(db_session, autor_id=autor.id)
    service = _service(db_session, storage, settings)

    with pytest.raises(TipoImagemInvalidoError):
        service.create(pedido.id, b"abc", "application/pdf", usuario=autor)

    assert storage.salvos == {}


def test_create_tamanho_excedido_levanta_413(
    db_session: Session, storage: _FakeStorage, settings: Settings
) -> None:
    """Conteúdo maior que `max_upload_bytes` levanta `ImagemMuitoGrandeError`."""
    autor = _criar_usuario(db_session, email="autor@x.com", papel=PapelUsuarioEnum.PROTETOR)
    pedido = _criar_pedido(db_session, autor_id=autor.id)
    service = _service(db_session, storage, settings)

    grande = b"x" * (settings.max_upload_bytes + 1)
    with pytest.raises(ImagemMuitoGrandeError):
        service.create(pedido.id, grande, "image/jpeg", usuario=autor)

    assert storage.salvos == {}


def test_create_limite_por_pedido_levanta_409(
    db_session: Session, storage: _FakeStorage, settings: Settings
) -> None:
    """Exceder `max_imagens_por_pedido` levanta `LimiteImagensExcedidoError`."""
    autor = _criar_usuario(db_session, email="autor@x.com", papel=PapelUsuarioEnum.PROTETOR)
    pedido = _criar_pedido(db_session, autor_id=autor.id)
    service = _service(db_session, storage, settings)

    service.create(pedido.id, b"a", "image/jpeg", usuario=autor)
    service.create(pedido.id, b"b", "image/jpeg", usuario=autor)  # atinge o limite (2)

    with pytest.raises(LimiteImagensExcedidoError):
        service.create(pedido.id, b"c", "image/jpeg", usuario=autor)


def test_list_by_pedido_publico(
    db_session: Session, storage: _FakeStorage, settings: Settings
) -> None:
    """`list_by_pedido` lista as imagens do pedido (sem exigir autor)."""
    autor = _criar_usuario(db_session, email="autor@x.com", papel=PapelUsuarioEnum.PROTETOR)
    pedido = _criar_pedido(db_session, autor_id=autor.id)
    service = _service(db_session, storage, settings)
    service.create(pedido.id, b"a", "image/jpeg", usuario=autor)

    imagens = service.list_by_pedido(pedido.id)
    assert len(imagens) == 1


def test_delete_remove_storage_e_linha(
    db_session: Session, storage: _FakeStorage, settings: Settings
) -> None:
    """`delete` remove o arquivo do storage e a linha do banco."""
    autor = _criar_usuario(db_session, email="autor@x.com", papel=PapelUsuarioEnum.PROTETOR)
    pedido = _criar_pedido(db_session, autor_id=autor.id)
    service = _service(db_session, storage, settings)
    imagem = service.create(pedido.id, b"a", "image/jpeg", usuario=autor)
    url = imagem.url

    service.delete(pedido.id, imagem.id, usuario=autor)

    assert url in storage.removidos
    assert service.list_by_pedido(pedido.id) == []


def test_delete_inexistente_levanta_404(
    db_session: Session, storage: _FakeStorage, settings: Settings
) -> None:
    """`delete` de imagem inexistente levanta `ImagemNotFoundError`."""
    autor = _criar_usuario(db_session, email="autor@x.com", papel=PapelUsuarioEnum.PROTETOR)
    pedido = _criar_pedido(db_session, autor_id=autor.id)
    service = _service(db_session, storage, settings)

    with pytest.raises(ImagemNotFoundError):
        service.delete(pedido.id, 99999, usuario=autor)


def test_delete_nao_autor_levanta_403(
    db_session: Session, storage: _FakeStorage, settings: Settings
) -> None:
    """`delete` por usuário que não é autor nem admin levanta `AcessoNegadoError`."""
    autor = _criar_usuario(db_session, email="autor@x.com", papel=PapelUsuarioEnum.PROTETOR)
    outro = _criar_usuario(db_session, email="outro@x.com", papel=PapelUsuarioEnum.PROTETOR)
    pedido = _criar_pedido(db_session, autor_id=autor.id)
    service = _service(db_session, storage, settings)
    imagem = service.create(pedido.id, b"a", "image/jpeg", usuario=autor)

    with pytest.raises(AcessoNegadoError):
        service.delete(pedido.id, imagem.id, usuario=outro)

    assert storage.removidos == []
