"""Testes do seed de dados de exemplo (`app.seed`)."""

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.storage import StorageBackend
from app.models.enums import PapelUsuarioEnum
from app.models.imagem import ImagemPedido
from app.models.pedido import PedidoAjuda
from app.models.usuario import Usuario
from app.seed import semear


class _FakeStorage(StorageBackend):
    """Storage em memória: evita I/O de disco/rede nos testes do seed.

    Guarda os bytes gravados por nome de arquivo e devolve uma URL pública
    estável, exercendo o mesmo contrato de `StorageBackend` sem efeitos no
    sistema de arquivos.
    """

    def __init__(self) -> None:
        self.gravados: dict[str, bytes] = {}

    def salvar(self, conteudo: bytes, nome_arquivo: str) -> str:
        self.gravados[nome_arquivo] = conteudo
        return f"https://cdn.test/{nome_arquivo}"

    def remover(self, url: str) -> None:
        nome = url.rsplit("/", 1)[-1]
        self.gravados.pop(nome, None)


@pytest.fixture
def fake_storage() -> _FakeStorage:
    """Storage em memória reutilizável pelos testes do seed."""
    return _FakeStorage()


def test_semear_cria_registros_de_exemplo(db_session: Session, fake_storage: _FakeStorage) -> None:
    """O seed popula usuários, pedidos e atendimentos de exemplo."""
    resumo = semear(db_session, storage=fake_storage)

    total_usuarios = db_session.scalar(select(func.count()).select_from(Usuario))
    total_pedidos = db_session.scalar(select(func.count()).select_from(PedidoAjuda))

    assert total_usuarios >= 2
    assert total_pedidos >= 1
    assert resumo["usuarios"] >= 2
    assert resumo["pedidos"] >= 1
    assert resumo["atendimentos"] >= 1


def test_semear_cria_um_admin(db_session: Session, fake_storage: _FakeStorage) -> None:
    """O seed cria ao menos um usuário com papel ADMIN."""
    semear(db_session, storage=fake_storage)

    admins = db_session.scalars(
        select(Usuario).where(Usuario.papel == PapelUsuarioEnum.ADMIN)
    ).all()

    assert len(admins) >= 1


def test_semear_anexa_imagem_de_capa_a_cada_pedido(
    db_session: Session, fake_storage: _FakeStorage
) -> None:
    """Cada pedido de exemplo recebe ao menos uma imagem de capa (via storage)."""
    resumo = semear(db_session, storage=fake_storage)

    pedidos = db_session.scalars(select(PedidoAjuda)).all()
    assert pedidos, "o seed deveria criar pedidos"

    for pedido in pedidos:
        imagens = db_session.scalars(
            select(ImagemPedido).where(ImagemPedido.pedido_id == pedido.id)
        ).all()
        assert len(imagens) >= 1, f"pedido {pedido.id} ficou sem imagem de capa"
        assert imagens[0].url.startswith("https://cdn.test/")

    # Uma imagem efetivamente gravada por pedido criado, e bytes não vazios.
    assert resumo["imagens"] == len(pedidos)
    assert fake_storage.gravados, "nenhum byte foi gravado no storage"
    assert all(len(conteudo) > 0 for conteudo in fake_storage.gravados.values())


def test_semear_e_idempotente(db_session: Session, fake_storage: _FakeStorage) -> None:
    """Rodar o seed duas vezes não duplica registros (incluindo imagens)."""
    semear(db_session, storage=fake_storage)
    total_usuarios_1 = db_session.scalar(select(func.count()).select_from(Usuario))
    total_pedidos_1 = db_session.scalar(select(func.count()).select_from(PedidoAjuda))
    total_imagens_1 = db_session.scalar(select(func.count()).select_from(ImagemPedido))

    resumo_2 = semear(db_session, storage=fake_storage)
    total_usuarios_2 = db_session.scalar(select(func.count()).select_from(Usuario))
    total_pedidos_2 = db_session.scalar(select(func.count()).select_from(PedidoAjuda))
    total_imagens_2 = db_session.scalar(select(func.count()).select_from(ImagemPedido))

    assert total_usuarios_2 == total_usuarios_1
    assert total_pedidos_2 == total_pedidos_1
    assert total_imagens_2 == total_imagens_1
    # Nada novo é criado na segunda passagem.
    assert resumo_2["usuarios"] == 0
    assert resumo_2["pedidos"] == 0
    assert resumo_2["atendimentos"] == 0
    assert resumo_2["imagens"] == 0
