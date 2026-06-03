"""Repositório de DoadorVoluntario."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.doador import DoadorVoluntario
from app.schemas import DoadorCreate, DoadorUpdate


class DoadorRepository:
    """Operações de persistência para `DoadorVoluntario`."""

    def __init__(self, session: Session) -> None:
        """Inicializa o repositório com uma sessão SQLAlchemy.

        Args:
            session: sessão ativa de banco.
        """
        self.session = session

    def create(self, payload: DoadorCreate) -> DoadorVoluntario:
        """Cria e persiste um doador.

        Args:
            payload: dados validados.

        Returns:
            Doador com `id` preenchido.
        """
        doador = DoadorVoluntario(**payload.model_dump())
        self.session.add(doador)
        self.session.commit()
        self.session.refresh(doador)
        return doador

    def get_by_id(self, doador_id: int) -> DoadorVoluntario | None:
        """Busca um doador pelo id.

        Args:
            doador_id: identificador.

        Returns:
            Doador ou None.
        """
        return self.session.get(DoadorVoluntario, doador_id)

    def get_by_email(self, email: str) -> DoadorVoluntario | None:
        """Busca um doador pelo e-mail.

        Args:
            email: e-mail de contato do doador.

        Returns:
            Doador com o e-mail informado, ou None se não existir.
        """
        stmt = select(DoadorVoluntario).where(DoadorVoluntario.email == email)
        return self.session.scalars(stmt).first()

    def find_or_create_by_email(
        self,
        *,
        nome: str,
        email: str,
        telefone: str | None = None,
        consentimento_aceito: bool = False,
        consentimento_versao: str | None = None,
        consentimento_em=None,
        commit: bool = True,
    ) -> DoadorVoluntario:
        """Retorna o doador com o e-mail informado, criando-o se não existir.

        Evita doadores órfãos/duplicados ao derivar o doador do usuário
        autenticado: um único doador por e-mail. Suporta composição transacional
        via `commit=False` (apenas flush) para uso dentro de uma transação maior.

        Args:
            nome: nome do doador (usado apenas na criação).
            email: e-mail de contato (chave de busca; único).
            telefone: telefone de contato (opcional, usado apenas na criação).
            consentimento_aceito: aceite LGPD (usado apenas na criação).
            consentimento_versao: versão do termo aceito (opcional).
            consentimento_em: instante do aceite (opcional).
            commit: se True, confirma a transação; se False, apenas faz flush.

        Returns:
            Doador existente ou recém-criado, com `id` preenchido.
        """
        existente = self.get_by_email(email)
        if existente is not None:
            return existente
        doador = DoadorVoluntario(
            nome=nome,
            email=email,
            telefone=telefone,
            consentimento_aceito=consentimento_aceito,
            consentimento_versao=consentimento_versao,
            consentimento_em=consentimento_em,
        )
        self.session.add(doador)
        if commit:
            self.session.commit()
        else:
            self.session.flush()
        self.session.refresh(doador)
        return doador

    def update(self, doador_id: int, payload: DoadorUpdate) -> DoadorVoluntario | None:
        """Atualiza parcialmente um doador.

        Args:
            doador_id: identificador.
            payload: campos a atualizar.

        Returns:
            Doador atualizado ou None.
        """
        doador = self.session.get(DoadorVoluntario, doador_id)
        if doador is None:
            return None
        for campo, valor in payload.model_dump(exclude_unset=True).items():
            setattr(doador, campo, valor)
        self.session.commit()
        self.session.refresh(doador)
        return doador
