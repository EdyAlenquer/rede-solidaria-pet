"""Seed idempotente de dados de exemplo (PT-BR) para a Rede Solidária Pet.

Popula a base com alguns usuários (incluindo um administrador), pedidos variados
(cidade, categoria, urgência e atributos do animal) e alguns atendimentos,
reutilizando os serviços e repositórios da aplicação. É idempotente: registros
já existentes (identificados por e-mail, para usuários, e por título, para
pedidos) não são recriados.

Uso como módulo executável:

    python -m app.seed

Side Effects:
    Persiste registros de exemplo no banco apontado por `DATABASE_URL`.
"""

from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.core.notifications import Notifier
from app.core.storage import StorageBackend, get_storage
from app.models.atendimento import AtendimentoPedido
from app.models.doador import DoadorVoluntario
from app.models.enums import (
    CategoriaEnum,
    EspecieEnum,
    PapelUsuarioEnum,
    PorteEnum,
    SexoEnum,
    StatusPedidoEnum,
    UrgenciaEnum,
)
from app.models.pedido import PedidoAjuda
from app.repositories.atendimento_repository import AtendimentoRepository
from app.repositories.doador_repository import DoadorRepository
from app.repositories.imagem_repository import ImagemRepository
from app.repositories.pedido_repository import PedidoRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas import AtendimentoCreate, PedidoCreate, PedidoStatusUpdate, UsuarioCreate
from app.services.atendimento_service import AtendimentoService
from app.services.imagem_service import ImagemService
from app.services.pedido_service import PedidoService
from app.services.usuario_service import UsuarioService

logger = logging.getLogger(__name__)

#: Versão do termo de consentimento registrada nos dados de exemplo.
_CONSENTIMENTO_VERSAO = "seed-1"

#: Diretório com as fotos de exemplo (domínio público / CC0) usadas como capa
#: dos pedidos do seed. Veja `seed_assets/CREDITS.md` para a procedência/licença.
_ASSETS_DIR = Path(__file__).resolve().parent / "seed_assets"

#: Content-type das fotos de exemplo (todas JPEG).
_IMAGEM_CONTENT_TYPE = "image/jpeg"


class _NotifierSilencioso(Notifier):
    """Notifier no-op usado durante o seed para não emitir alertas reais.

    O seed cria atendimentos em lote; notificar a cada um poluiria o log (ou,
    com backend SMTP, dispararia e-mails indesejados). Este notifier descarta a
    notificação silenciosamente.
    """

    def notificar_novo_atendimento(
        self, *, pedido, atendimento, doador
    ) -> None:  # noqa: ANN001, ARG002
        """Ignora a notificação (no-op).

        Args:
            pedido: pedido atendido (ignorado).
            atendimento: atendimento criado (ignorado).
            doador: doador do atendimento (ignorado).
        """
        return None


#: Usuários de exemplo. O primeiro é promovido a administrador.
_USUARIOS: list[dict[str, str]] = [
    {
        "nome": "Marina Souza",
        "email": "marina.admin@redesolidariapet.org",
        "senha": "seed-admin-123",
        "telefone": "11999990001",
        "papel": PapelUsuarioEnum.ADMIN,
    },
    {
        "nome": "João Pereira",
        "email": "joao.protetor@redesolidariapet.org",
        "senha": "seed-protetor-123",
        "telefone": "11999990002",
        "papel": PapelUsuarioEnum.PROTETOR,
    },
    {
        "nome": "Ana Lima",
        "email": "ana.protetora@redesolidariapet.org",
        "senha": "seed-protetor-456",
        "telefone": "21999990003",
        "papel": PapelUsuarioEnum.PROTETOR,
    },
    {
        "nome": "Carlos Mendes",
        "email": "carlos.voluntario@redesolidariapet.org",
        "senha": "seed-voluntario-789",
        "telefone": "31999990004",
        "papel": PapelUsuarioEnum.PROTETOR,
    },
]


#: Pedidos de exemplo, com o e-mail do autor para vincular após criar usuários.
_PEDIDOS: list[dict] = [
    {
        "autor_email": "joao.protetor@redesolidariapet.org",
        "titulo": "Ração para cães resgatados na zona leste",
        "descricao": "Resgatamos cinco cães e precisamos de ração para mantê-los nesta semana.",
        "categoria": CategoriaEnum.RACAO,
        "urgencia": UrgenciaEnum.ALTA,
        "cidade": "São Paulo",
        "estado": "SP",
        "bairro": "Itaquera",
        "latitude": -23.5405,
        "longitude": -46.4717,
        "especie": EspecieEnum.CAO,
        "porte": PorteEnum.MEDIO,
        "sexo": SexoEnum.DESCONHECIDO,
        "quantidade": 5,
        "contato": "11999990002",
        "status": StatusPedidoEnum.ABERTO,
        "imagem": "pedido-1-cao.jpg",
    },
    {
        "autor_email": "ana.protetora@redesolidariapet.org",
        "titulo": "Transporte de gata para consulta veterinária",
        "descricao": "Gata precisa ir até a clínica parceira no centro para uma consulta amanhã.",
        "categoria": CategoriaEnum.TRANSPORTE,
        "urgencia": UrgenciaEnum.MEDIA,
        "cidade": "Rio de Janeiro",
        "estado": "RJ",
        "bairro": "Tijuca",
        "latitude": -22.9249,
        "longitude": -43.2277,
        "especie": EspecieEnum.GATO,
        "porte": PorteEnum.PEQUENO,
        "sexo": SexoEnum.FEMEA,
        "idade_aproximada": "2 anos",
        "quantidade": 1,
        "contato": "21999990003",
        "status": StatusPedidoEnum.ABERTO,
        "imagem": "pedido-2-gato.jpg",
    },
    {
        "autor_email": "joao.protetor@redesolidariapet.org",
        "titulo": "Atendimento veterinário urgente para cão atropelado",
        "descricao": "Cão foi atropelado e precisa de atendimento veterinário de emergência.",
        "categoria": CategoriaEnum.VETERINARIO,
        "urgencia": UrgenciaEnum.ALTA,
        "cidade": "Belo Horizonte",
        "estado": "MG",
        "bairro": "Savassi",
        "latitude": -19.9386,
        "longitude": -43.9344,
        "especie": EspecieEnum.CAO,
        "porte": PorteEnum.GRANDE,
        "sexo": SexoEnum.MACHO,
        "idade_aproximada": "adulto",
        "quantidade": 1,
        "contato": "11999990002",
        "status": StatusPedidoEnum.ABERTO,
        "imagem": "pedido-3-cao.jpg",
    },
    {
        "autor_email": "ana.protetora@redesolidariapet.org",
        "titulo": "Lar temporário para ninhada de gatinhos",
        "descricao": "Quatro gatinhos órfãos precisam de um lar temporário até a adoção.",
        "categoria": CategoriaEnum.LAR_TEMPORARIO,
        "urgencia": UrgenciaEnum.BAIXA,
        "cidade": "Curitiba",
        "estado": "PR",
        "bairro": "Batel",
        "latitude": -25.4420,
        "longitude": -49.2870,
        "especie": EspecieEnum.GATO,
        "porte": PorteEnum.PEQUENO,
        "sexo": SexoEnum.DESCONHECIDO,
        "idade_aproximada": "2 meses",
        "quantidade": 4,
        "contato": "21999990003",
        "status": StatusPedidoEnum.CONCLUIDO,
        "imagem": "pedido-4-gato.jpg",
    },
    {
        "autor_email": "joao.protetor@redesolidariapet.org",
        "titulo": "Resgate de cão preso em terreno baldio",
        "descricao": "Cão está preso em um terreno baldio e precisa de resgate com segurança.",
        "categoria": CategoriaEnum.RESGATE,
        "urgencia": UrgenciaEnum.ALTA,
        "cidade": "Porto Alegre",
        "estado": "RS",
        "bairro": "Cidade Baixa",
        "latitude": -30.0420,
        "longitude": -51.2230,
        "especie": EspecieEnum.CAO,
        "porte": PorteEnum.MEDIO,
        "sexo": SexoEnum.MACHO,
        "quantidade": 1,
        "contato": "11999990002",
        "status": StatusPedidoEnum.CANCELADO,
        "imagem": "pedido-5-cao.jpg",
    },
]


#: Atendimentos de exemplo: voluntário que ajuda em pedidos por título.
_ATENDIMENTOS: list[dict[str, str]] = [
    {
        "doador_email": "carlos.voluntario@redesolidariapet.org",
        "pedido_titulo": "Ração para cães resgatados na zona leste",
        "tipo_ajuda": "doacao_racao",
        "observacao": "Posso doar dois sacos de ração de 15kg ainda esta semana.",
    },
    {
        "doador_email": "carlos.voluntario@redesolidariapet.org",
        "pedido_titulo": "Transporte de gata para consulta veterinária",
        "tipo_ajuda": "transporte",
        "observacao": "Tenho carro e levo a gatinha até a clínica amanhã de manhã.",
    },
]


def _semear_usuarios(service: UsuarioService) -> tuple[dict[str, int], int]:
    """Cria os usuários de exemplo, promovendo o admin, de forma idempotente.

    Args:
        service: serviço de usuários ligado à sessão do seed.

    Returns:
        Tupla com o mapa `email -> id` de todos os usuários de exemplo (criados
        ou já existentes) e a contagem dos que foram efetivamente criados.

    Side Effects:
        Persiste usuários ausentes e ajusta o papel do administrador.
    """
    ids_por_email: dict[str, int] = {}
    criados = 0
    for dados in _USUARIOS:
        existente = service.repository.get_by_email(dados["email"])
        if existente is not None:
            ids_por_email[dados["email"]] = existente.id
            continue
        usuario = service.create(
            UsuarioCreate(
                nome=dados["nome"],
                email=dados["email"],
                senha=dados["senha"],
                telefone=dados["telefone"],
                consentimento_aceito=True,
                consentimento_versao=_CONSENTIMENTO_VERSAO,
            )
        )
        if dados["papel"] is PapelUsuarioEnum.ADMIN:
            usuario.papel = PapelUsuarioEnum.ADMIN
            service.repository.session.commit()
        ids_por_email[dados["email"]] = usuario.id
        criados += 1
    return ids_por_email, criados


def _pedido_por_titulo(session: Session, titulo: str) -> PedidoAjuda | None:
    """Busca um pedido de exemplo pelo título exato (chave de idempotência).

    Args:
        session: sessão ativa do seed.
        titulo: título do pedido procurado.

    Returns:
        Pedido com o título informado, ou None se não existir.
    """
    stmt = select(PedidoAjuda).where(PedidoAjuda.titulo == titulo)
    return session.scalars(stmt).first()


def _semear_pedidos(
    service: PedidoService,
    session: Session,
    ids_por_email: dict[str, int],
) -> tuple[dict[str, int], int]:
    """Cria os pedidos de exemplo e ajusta seus status, de forma idempotente.

    Args:
        service: serviço de pedidos ligado à sessão do seed.
        session: sessão ativa do seed (para checagem por título).
        ids_por_email: mapa `email -> id` dos autores.

    Returns:
        Tupla com o mapa `titulo -> id` de todos os pedidos de exemplo e a
        contagem dos que foram efetivamente criados.

    Side Effects:
        Persiste pedidos ausentes e aplica o status declarado em cada um.
    """
    ids_por_titulo: dict[str, int] = {}
    criados = 0
    for dados in _PEDIDOS:
        existente = _pedido_por_titulo(session, dados["titulo"])
        if existente is not None:
            ids_por_titulo[dados["titulo"]] = existente.id
            continue
        autor_id = ids_por_email[dados["autor_email"]]
        payload = PedidoCreate(
            titulo=dados["titulo"],
            descricao=dados["descricao"],
            categoria=dados["categoria"],
            urgencia=dados["urgencia"],
            cidade=dados["cidade"],
            estado=dados["estado"],
            bairro=dados.get("bairro"),
            latitude=dados.get("latitude"),
            longitude=dados.get("longitude"),
            especie=dados.get("especie"),
            porte=dados.get("porte"),
            sexo=dados.get("sexo"),
            idade_aproximada=dados.get("idade_aproximada"),
            quantidade=dados.get("quantidade", 1),
            contato=dados["contato"],
            consentimento_aceito=True,
            consentimento_versao=_CONSENTIMENTO_VERSAO,
        )
        pedido = service.create(payload, autor_id=autor_id)
        status = dados["status"]
        if status is not StatusPedidoEnum.ABERTO:
            _aplicar_status(service, pedido.id, status)
        ids_por_titulo[dados["titulo"]] = pedido.id
        criados += 1
    return ids_por_titulo, criados


def _aplicar_status(service: PedidoService, pedido_id: int, status_final: StatusPedidoEnum) -> None:
    """Leva um pedido recém-criado (ABERTO) até o status final desejado.

    Respeita a máquina de estados do `PedidoService`: para CONCLUIDO é preciso
    passar por EM_ANDAMENTO; CANCELADO é alcançável direto de ABERTO.

    Args:
        service: serviço de pedidos.
        pedido_id: id do pedido a transicionar.
        status_final: status desejado ao fim das transições.

    Side Effects:
        Persiste as mudanças de status do pedido.
    """
    if status_final is StatusPedidoEnum.CONCLUIDO:
        transicoes = [StatusPedidoEnum.EM_ANDAMENTO, StatusPedidoEnum.CONCLUIDO]
    else:
        transicoes = [status_final]
    # O autor é dono do pedido; usa-se o admin de exemplo para autorizar a
    # transição independentemente do autor.
    admin = service.repository.session.scalars(
        select(_usuario_model()).where(_usuario_model().papel == PapelUsuarioEnum.ADMIN)
    ).first()
    for status in transicoes:
        service.change_status(pedido_id, PedidoStatusUpdate(status=status), usuario=admin)


def _usuario_model():
    """Retorna o modelo `Usuario` (import tardio evita ciclo no topo).

    Returns:
        Classe ORM `Usuario`.
    """
    from app.models.usuario import Usuario

    return Usuario


def _semear_atendimentos(
    service: AtendimentoService,
    session: Session,
    ids_por_email: dict[str, int],
    ids_por_titulo: dict[str, int],
) -> int:
    """Cria os atendimentos de exemplo de forma idempotente.

    Idempotência: pula o atendimento quando já existe um para o mesmo par
    (pedido, doador derivado do e-mail do voluntário).

    Args:
        service: serviço de atendimentos ligado à sessão do seed.
        session: sessão ativa do seed.
        ids_por_email: mapa `email -> id` dos usuários.
        ids_por_titulo: mapa `titulo -> id` dos pedidos.

    Returns:
        Quantidade de atendimentos efetivamente criados.

    Side Effects:
        Persiste atendimentos ausentes (pode transicionar pedidos ABERTO ->
        EM_ANDAMENTO via serviço).
    """
    criados = 0
    for dados in _ATENDIMENTOS:
        pedido_id = ids_por_titulo[dados["pedido_titulo"]]
        usuario = session.get(_usuario_model(), ids_por_email[dados["doador_email"]])
        if _atendimento_ja_existe(session, pedido_id, usuario.email):
            continue
        service.create(
            pedido_id,
            AtendimentoCreate(
                tipo_ajuda=dados["tipo_ajuda"],
                observacao=dados["observacao"],
            ),
            usuario=usuario,
        )
        criados += 1
    return criados


def _atendimento_ja_existe(session: Session, pedido_id: int, doador_email: str) -> bool:
    """Indica se já há atendimento do doador (por e-mail) no pedido.

    Args:
        session: sessão ativa do seed.
        pedido_id: id do pedido.
        doador_email: e-mail do doador (derivado do voluntário).

    Returns:
        True se já existir um atendimento desse doador no pedido.
    """
    doador = session.scalars(
        select(DoadorVoluntario).where(DoadorVoluntario.email == doador_email)
    ).first()
    if doador is None:
        return False
    stmt = select(AtendimentoPedido).where(
        AtendimentoPedido.pedido_id == pedido_id,
        AtendimentoPedido.doador_id == doador.id,
    )
    return session.scalars(stmt).first() is not None


def _semear_imagens(
    service: ImagemService,
    imagem_repo: ImagemRepository,
    session: Session,
    ids_por_titulo: dict[str, int],
) -> int:
    """Anexa uma foto de capa (CC0) a cada pedido de exemplo, de forma idempotente.

    A foto é gravada pelo `StorageBackend` injetado — disco local em
    desenvolvimento, object storage S3/R2 em produção — e referenciada por uma
    linha `ImagemPedido`, exatamente como no upload via API. Sem isso, os cards
    do feed caem no placeholder e o usuário não vê nenhuma imagem.

    Idempotência: pedidos que já têm ao menos uma imagem são pulados, então
    rodar o seed novamente (ou sobre uma base já semeada) não duplica fotos.

    Args:
        service: serviço de imagens ligado à sessão e ao storage do seed.
        imagem_repo: repositório de imagens (checagem de idempotência).
        session: sessão ativa do seed (para localizar o admin autorizador).
        ids_por_titulo: mapa `titulo -> id` dos pedidos de exemplo.

    Returns:
        Quantidade de imagens efetivamente criadas nesta execução.

    Side Effects:
        Grava os arquivos no storage e insere linhas em `imagens_pedido`.
    """
    admin = session.scalars(
        select(_usuario_model()).where(_usuario_model().papel == PapelUsuarioEnum.ADMIN)
    ).first()
    criadas = 0
    for dados in _PEDIDOS:
        nome_arquivo = dados.get("imagem")
        if not nome_arquivo:
            continue
        pedido_id = ids_por_titulo[dados["titulo"]]
        if imagem_repo.count_by_pedido(pedido_id) > 0:
            continue
        conteudo = (_ASSETS_DIR / nome_arquivo).read_bytes()
        service.create(pedido_id, conteudo, _IMAGEM_CONTENT_TYPE, usuario=admin)
        criadas += 1
    return criadas


def semear(
    session: Session,
    *,
    storage: StorageBackend | None = None,
    settings: Settings | None = None,
) -> dict[str, int]:
    """Popula a base com dados de exemplo, de forma idempotente.

    Args:
        session: sessão SQLAlchemy ativa onde os dados serão criados.
        storage: backend de armazenamento das fotos de capa. Quando omitido,
            é resolvido por `get_storage(settings)` (disco local por padrão; em
            produção, o object storage configurado por ambiente). Testes podem
            injetar um storage em memória para evitar I/O.
        settings: configurações da aplicação (limites/tipos de upload e seleção
            de storage). Quando omitido, usa `get_settings()`.

    Returns:
        Resumo com a quantidade de registros efetivamente criados nesta
        execução, nas chaves `usuarios`, `pedidos`, `atendimentos` e `imagens`.

    Side Effects:
        Persiste usuários, pedidos, atendimentos e fotos de capa ausentes
        (as fotos também são gravadas no storage).
    """
    settings = settings or get_settings()
    storage = storage if storage is not None else get_storage(settings)

    usuario_repo = UsuarioRepository(session)
    pedido_repo = PedidoRepository(session)
    atendimento_repo = AtendimentoRepository(session)
    doador_repo = DoadorRepository(session)
    imagem_repo = ImagemRepository(session)

    usuario_service = UsuarioService(usuario_repo)
    pedido_service = PedidoService(pedido_repo)
    atendimento_service = AtendimentoService(
        atendimento_repo,
        pedido_repo,
        doador_repo,
        notifier=_NotifierSilencioso(),
    )
    imagem_service = ImagemService(
        imagem_repo,
        pedido_repo,
        storage=storage,
        settings=settings,
    )

    ids_por_email, usuarios_criados = _semear_usuarios(usuario_service)
    ids_por_titulo, pedidos_criados = _semear_pedidos(pedido_service, session, ids_por_email)
    atendimentos_criados = _semear_atendimentos(
        atendimento_service, session, ids_por_email, ids_por_titulo
    )
    imagens_criadas = _semear_imagens(imagem_service, imagem_repo, session, ids_por_titulo)

    return {
        "usuarios": usuarios_criados,
        "pedidos": pedidos_criados,
        "atendimentos": atendimentos_criados,
        "imagens": imagens_criadas,
    }


def main() -> None:
    """Ponto de entrada de `python -m app.seed`.

    Abre uma sessão a partir de `SessionLocal`, executa o seed e registra um
    resumo no log.

    Side Effects:
        Persiste os dados de exemplo no banco configurado.
    """
    logging.basicConfig(level=logging.INFO)
    from app.database import SessionLocal

    session = SessionLocal()
    try:
        resumo = semear(session)
    finally:
        session.close()
    logger.info(
        "Seed concluído: %s usuários, %s pedidos, %s atendimentos, %s imagens criados.",
        resumo["usuarios"],
        resumo["pedidos"],
        resumo["atendimentos"],
        resumo["imagens"],
    )


if __name__ == "__main__":
    main()
