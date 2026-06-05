"""Testes unitários do repositório de imagens de pedido."""

from sqlalchemy.orm import Session

from app.models.enums import CategoriaEnum, UrgenciaEnum
from app.models.pedido import PedidoAjuda
from app.repositories.imagem_repository import ImagemRepository


def _criar_pedido(db: Session) -> PedidoAjuda:
    """Cria e persiste um pedido mínimo para os testes.

    Args:
        db: sessão de teste.

    Returns:
        Pedido persistido.
    """
    pedido = PedidoAjuda(
        titulo="Pedido",
        descricao="Descrição do pedido de teste.",
        categoria=CategoriaEnum.RESGATE,
        urgencia=UrgenciaEnum.ALTA,
        contato="11999990000",
        cidade="São Paulo",
        estado="SP",
    )
    db.add(pedido)
    db.commit()
    db.refresh(pedido)
    return pedido


def test_create_atribui_ordem_sequencial(db_session: Session) -> None:
    """Cada imagem criada recebe a próxima `ordem` disponível no pedido."""
    pedido = _criar_pedido(db_session)
    repo = ImagemRepository(db_session)

    primeira = repo.create(pedido.id, url="/uploads/a.jpg")
    segunda = repo.create(pedido.id, url="/uploads/b.jpg")

    assert primeira.ordem == 0
    assert segunda.ordem == 1


def test_list_by_pedido_retorna_ordenado_por_ordem(db_session: Session) -> None:
    """`list_by_pedido` devolve as imagens ordenadas por `ordem` crescente."""
    pedido = _criar_pedido(db_session)
    repo = ImagemRepository(db_session)
    repo.create(pedido.id, url="/uploads/a.jpg")
    repo.create(pedido.id, url="/uploads/b.jpg")

    imagens = repo.list_by_pedido(pedido.id)

    assert [img.url for img in imagens] == ["/uploads/a.jpg", "/uploads/b.jpg"]
    assert [img.ordem for img in imagens] == [0, 1]


def test_count_by_pedido(db_session: Session) -> None:
    """`count_by_pedido` conta as imagens vinculadas ao pedido."""
    pedido = _criar_pedido(db_session)
    repo = ImagemRepository(db_session)
    assert repo.count_by_pedido(pedido.id) == 0

    repo.create(pedido.id, url="/uploads/a.jpg")
    assert repo.count_by_pedido(pedido.id) == 1


def test_get_by_id_filtra_por_pedido(db_session: Session) -> None:
    """`get_by_id` só retorna a imagem se ela pertencer ao pedido informado."""
    pedido = _criar_pedido(db_session)
    outro = _criar_pedido(db_session)
    repo = ImagemRepository(db_session)
    imagem = repo.create(pedido.id, url="/uploads/a.jpg")

    assert repo.get_by_id(pedido.id, imagem.id) is imagem
    assert repo.get_by_id(outro.id, imagem.id) is None
    assert repo.get_by_id(pedido.id, 99999) is None


def test_delete_remove_a_linha(db_session: Session) -> None:
    """`delete` remove a imagem e ela deixa de aparecer na listagem."""
    pedido = _criar_pedido(db_session)
    repo = ImagemRepository(db_session)
    imagem = repo.create(pedido.id, url="/uploads/a.jpg")

    repo.delete(imagem)

    assert repo.count_by_pedido(pedido.id) == 0
