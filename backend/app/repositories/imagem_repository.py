"""Repositório de ImagemPedido."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.imagem import ImagemPedido


class ImagemRepository:
    """Operações de persistência para `ImagemPedido`."""

    def __init__(self, session: Session) -> None:
        """Inicializa o repositório com uma sessão.

        Args:
            session: sessão SQLAlchemy ativa.
        """
        self.session = session

    def count_by_pedido(self, pedido_id: int) -> int:
        """Conta as imagens vinculadas a um pedido.

        Args:
            pedido_id: id do pedido.

        Returns:
            Quantidade de imagens do pedido.
        """
        stmt = select(func.count(ImagemPedido.id)).where(ImagemPedido.pedido_id == pedido_id)
        return int(self.session.scalar(stmt) or 0)

    def _proxima_ordem(self, pedido_id: int) -> int:
        """Calcula a próxima posição de exibição livre para o pedido.

        Args:
            pedido_id: id do pedido.

        Returns:
            `max(ordem) + 1` das imagens existentes, ou 0 se não houver nenhuma.
        """
        stmt = select(func.max(ImagemPedido.ordem)).where(ImagemPedido.pedido_id == pedido_id)
        maior = self.session.scalar(stmt)
        return 0 if maior is None else int(maior) + 1

    def create(self, pedido_id: int, *, url: str, commit: bool = True) -> ImagemPedido:
        """Persiste uma nova imagem para o pedido, na próxima `ordem` disponível.

        Args:
            pedido_id: id do pedido dono da imagem.
            url: URL pública da imagem já gravada no storage.
            commit: se True, confirma a transação; se False, apenas faz flush
                para permitir composição transacional pela camada de serviço.

        Returns:
            Imagem persistida com `id`, `ordem` e `criado_em`.

        Raises:
            sqlalchemy.exc.IntegrityError: se `pedido_id` não existir (com o
                pragma de FK ativo).
        """
        imagem = ImagemPedido(
            pedido_id=pedido_id,
            url=url,
            ordem=self._proxima_ordem(pedido_id),
        )
        self.session.add(imagem)
        if commit:
            self.session.commit()
        else:
            self.session.flush()
        self.session.refresh(imagem)
        return imagem

    def list_by_pedido(self, pedido_id: int) -> list[ImagemPedido]:
        """Lista as imagens de um pedido, ordenadas por `ordem` crescente.

        Args:
            pedido_id: id do pedido.

        Returns:
            Lista de imagens ordenada por posição de exibição.
        """
        stmt = (
            select(ImagemPedido)
            .where(ImagemPedido.pedido_id == pedido_id)
            .order_by(ImagemPedido.ordem.asc(), ImagemPedido.id.asc())
        )
        return list(self.session.scalars(stmt).all())

    def get_by_id(self, pedido_id: int, imagem_id: int) -> ImagemPedido | None:
        """Busca uma imagem garantindo que pertença ao pedido informado.

        Args:
            pedido_id: id do pedido dono esperado.
            imagem_id: id da imagem.

        Returns:
            Imagem encontrada e vinculada ao pedido, ou None caso contrário.
        """
        stmt = select(ImagemPedido).where(
            ImagemPedido.id == imagem_id,
            ImagemPedido.pedido_id == pedido_id,
        )
        return self.session.scalar(stmt)

    def delete(self, imagem: ImagemPedido, *, commit: bool = True) -> None:
        """Remove a linha da imagem do banco.

        Args:
            imagem: instância a remover.
            commit: se True, confirma a transação; se False, apenas faz flush.

        Side Effects:
            Apaga a imagem da tabela `imagens_pedido`.
        """
        self.session.delete(imagem)
        if commit:
            self.session.commit()
        else:
            self.session.flush()
