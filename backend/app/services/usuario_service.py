"""Serviço de domínio para Usuario (registro, autenticação e direitos LGPD)."""

import secrets
from datetime import UTC, datetime

from app.core.errors import EmailJaCadastradoError, UsuarioNotFoundError
from app.core.security import hash_senha, verificar_senha
from app.models.atendimento import AtendimentoPedido
from app.models.enums import PapelUsuarioEnum
from app.models.pedido import PedidoAjuda
from app.models.usuario import Usuario
from app.repositories.atendimento_repository import AtendimentoRepository
from app.repositories.doador_repository import DoadorRepository
from app.repositories.pedido_repository import PedidoRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas import UsuarioCreate


class UsuarioService:
    """Operações de negócio sobre `Usuario`.

    Além de registro e autenticação, concentra os direitos do titular (LGPD):
    exportação dos dados pessoais e anonimização/eliminação. As operações que
    cruzam pedidos e atendimentos exigem que os respectivos repositórios sejam
    injetados; quando ausentes, apenas as operações de usuário ficam disponíveis.
    """

    def __init__(
        self,
        repository: UsuarioRepository,
        *,
        pedido_repository: PedidoRepository | None = None,
        atendimento_repository: AtendimentoRepository | None = None,
        doador_repository: DoadorRepository | None = None,
    ) -> None:
        """Inicializa o serviço com o repositório de usuários e dependências LGPD.

        Args:
            repository: repositório de usuários (obrigatório).
            pedido_repository: repositório de pedidos; exigido pela exportação e
                pela anonimização (remoção dos pedidos do titular).
            atendimento_repository: repositório de atendimentos; exigido pela
                exportação (atendimentos do titular).
            doador_repository: repositório de doadores; exigido pela exportação
                para resolver o doador do titular pelo e-mail.
        """
        self.repository = repository
        self.pedido_repository = pedido_repository
        self.atendimento_repository = atendimento_repository
        self.doador_repository = doador_repository

    def create(self, payload: UsuarioCreate) -> Usuario:
        """Cria um usuário com papel `PROTETOR` e senha hasheada.

        Args:
            payload: dados validados de registro (senha em texto puro).

        Returns:
            Usuário criado com `id` preenchido.

        Raises:
            EmailJaCadastradoError: se o e-mail já pertencer a outro usuário.
        """
        if self.repository.get_by_email(payload.email) is not None:
            raise EmailJaCadastradoError(f"O e-mail {payload.email} já está cadastrado.")
        return self.repository.create(
            nome=payload.nome,
            email=payload.email,
            senha_hash=hash_senha(payload.senha),
            telefone=payload.telefone,
            papel=PapelUsuarioEnum.PROTETOR,
            consentimento_aceito=payload.consentimento_aceito,
            consentimento_versao=payload.consentimento_versao,
            consentimento_em=datetime.now(UTC) if payload.consentimento_aceito else None,
        )

    def autenticar(self, email: str, senha: str) -> Usuario | None:
        """Valida credenciais e retorna o usuário correspondente.

        Args:
            email: e-mail informado no login.
            senha: senha em texto puro informada no login.

        Returns:
            Usuário autenticado, ou None se o e-mail não existir ou a senha
            não conferir.
        """
        usuario = self.repository.get_by_email(email)
        if usuario is None:
            return None
        if not verificar_senha(senha, usuario.senha_hash):
            return None
        return usuario

    def get_by_id(self, usuario_id: int) -> Usuario:
        """Busca um usuário pelo id.

        Args:
            usuario_id: identificador.

        Returns:
            Usuário encontrado.

        Raises:
            UsuarioNotFoundError: se o usuário não existir ou estiver soft-deletado.
        """
        usuario = self.repository.get_by_id(usuario_id)
        if usuario is None:
            raise UsuarioNotFoundError(f"Usuário id={usuario_id} não existe.")
        return usuario

    def exportar_dados(self, usuario: Usuario) -> dict[str, object]:
        """Reúne os dados pessoais do titular para o direito de acesso (LGPD).

        Args:
            usuario: usuário autenticado cujos dados serão exportados.

        Returns:
            Dicionário com `perfil` (o próprio usuário), `pedidos` (pedidos ativos
            do usuário, com o contato próprio) e `atendimentos` (atendimentos do
            doador associado ao e-mail do usuário; vazio se não houver doador).

        Raises:
            RuntimeError: se os repositórios de pedidos/atendimentos/doadores não
                tiverem sido injetados no serviço.
        """
        if (
            self.pedido_repository is None
            or self.atendimento_repository is None
            or self.doador_repository is None
        ):
            raise RuntimeError(
                "Exportação exige pedido_repository, atendimento_repository e "
                "doador_repository injetados."
            )

        pedidos: list[PedidoAjuda] = self.pedido_repository.list_by_autor(usuario.id)
        atendimentos: list[AtendimentoPedido] = []
        doador = self.doador_repository.get_by_email(usuario.email)
        if doador is not None:
            atendimentos = self.atendimento_repository.list_by_doador(doador.id)
        return {"perfil": usuario, "pedidos": pedidos, "atendimentos": atendimentos}

    def anonimizar(self, usuario_id: int) -> Usuario:
        """Anonimiza e elimina o titular e seus pedidos, em uma única transação.

        Implementa o direito de eliminação (LGPD): anonimiza o usuário (nome,
        e-mail, telefone e senha), marca seu soft-delete e, quando o repositório
        de pedidos está disponível, soft-deleta os pedidos do titular anonimizando
        o `contato`. Tudo é confirmado atomicamente; em caso de erro, a transação
        é desfeita.

        Args:
            usuario_id: identificador do usuário a anonimizar.

        Returns:
            Usuário já anonimizado e soft-deletado.

        Raises:
            UsuarioNotFoundError: se o usuário não existir ou já estiver removido.

        Side Effects:
            Persiste a anonimização do usuário e a remoção de seus pedidos.
        """
        usuario = self.get_by_id(usuario_id)
        # Hash de uma senha aleatória que ninguém conhece: invalida o login sem
        # deixar a coluna NOT NULL vazia.
        senha_hash_anonima = hash_senha(secrets.token_urlsafe(32))
        try:
            usa_transacao = self.pedido_repository is not None
            self.repository.anonimizar(
                usuario,
                senha_hash_anonima=senha_hash_anonima,
                commit=not usa_transacao,
            )
            if self.pedido_repository is not None:
                self.pedido_repository.soft_delete_e_anonimizar_por_autor(usuario_id, commit=False)
                self.repository.session.commit()
        except Exception:
            self.repository.session.rollback()
            raise
        return usuario
