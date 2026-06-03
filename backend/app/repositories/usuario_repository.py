"""Repositório de Usuario."""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import PapelUsuarioEnum
from app.models.usuario import Usuario


class UsuarioRepository:
    """Operações de persistência para `Usuario`."""

    def __init__(self, session: Session) -> None:
        """Inicializa o repositório com uma sessão SQLAlchemy.

        Args:
            session: sessão ativa de banco.
        """
        self.session = session

    def create(
        self,
        *,
        nome: str,
        email: str,
        senha_hash: str,
        telefone: str | None,
        papel: PapelUsuarioEnum,
        consentimento_aceito: bool,
        consentimento_versao: str | None,
        consentimento_em: datetime | None = None,
    ) -> Usuario:
        """Cria e persiste um usuário a partir de campos já validados/hasheados.

        A senha deve chegar já como hash; este repositório nunca recebe senha em
        texto puro.

        Args:
            nome: nome do usuário.
            email: e-mail de login (único).
            senha_hash: hash argon2 da senha.
            telefone: telefone de contato (opcional).
            papel: papel do usuário.
            consentimento_aceito: aceite do termo LGPD.
            consentimento_versao: versão do termo aceito (opcional).
            consentimento_em: instante do aceite do termo (opcional).

        Returns:
            Usuário recém-criado com `id` preenchido.
        """
        usuario = Usuario(
            nome=nome,
            email=email,
            senha_hash=senha_hash,
            telefone=telefone,
            papel=papel,
            consentimento_aceito=consentimento_aceito,
            consentimento_versao=consentimento_versao,
            consentimento_em=consentimento_em,
        )
        self.session.add(usuario)
        self.session.commit()
        self.session.refresh(usuario)
        return usuario

    def get_by_id(self, usuario_id: int) -> Usuario | None:
        """Busca um usuário ativo (não soft-deletado) pelo id.

        Args:
            usuario_id: identificador.

        Returns:
            Usuário ativo ou None se inexistente/soft-deletado.
        """
        usuario = self.session.get(Usuario, usuario_id)
        if usuario is None or usuario.deleted_at is not None:
            return None
        return usuario

    def get_by_email(self, email: str) -> Usuario | None:
        """Busca um usuário ativo pelo e-mail.

        Args:
            email: e-mail de login.

        Returns:
            Usuário ativo com o e-mail informado, ou None.
        """
        stmt = select(Usuario).where(Usuario.email == email, Usuario.deleted_at.is_(None))
        return self.session.scalars(stmt).first()

    def anonimizar(
        self,
        usuario: Usuario,
        *,
        senha_hash_anonima: str,
        commit: bool = True,
    ) -> Usuario:
        """Anonimiza um usuário e marca seu soft-delete (direito de eliminação LGPD).

        Substitui os dados pessoais por valores anônimos e libera o e-mail
        original para reuso (o e-mail anônimo passa a ser único por id). A senha
        é invalidada por um hash que nunca corresponde a uma senha real.

        Args:
            usuario: usuário ativo a anonimizar (já carregado da sessão).
            senha_hash_anonima: hash que invalida a autenticação (gerado pela
                camada de serviço a partir de um segredo aleatório).
            commit: se True, confirma a transação; se False, apenas faz flush
                para permitir composição transacional pela camada de serviço.

        Returns:
            O próprio usuário, já anonimizado e soft-deletado.

        Side Effects:
            Altera os campos pessoais do usuário e preenche `deleted_at`.
        """
        usuario.nome = "Usuário removido"
        usuario.email = f"removido+{usuario.id}@anonimizado.local"
        usuario.telefone = None
        usuario.senha_hash = senha_hash_anonima
        usuario.deleted_at = func.now()
        if commit:
            self.session.commit()
        else:
            self.session.flush()
        return usuario
