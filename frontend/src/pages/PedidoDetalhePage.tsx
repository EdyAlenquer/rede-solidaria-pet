import { lazy, Suspense, useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'
import { Badge, Button, Modal, Select } from '../components/ui'
import { Seo } from '../components/Seo'
import { useToast } from '../components/Toast'
import {
  categorias,
  especies,
  motivosDenuncia,
  portes,
  rotuloDe,
  sexos,
  status as statusOpcoes,
  urgencias,
} from '../constants/dominio'
import { criarAtendimento, listarAtendimentos } from '../services/api/atendimentos'
import { denunciarPedido } from '../services/api/denuncias'
import {
  alterarStatusPedido,
  excluirPedido,
  obterPedido,
  revelarContato,
} from '../services/api/pedidos'
import { rotuloLocalizacao, temCoordenadas, tomUrgencia } from '../utils/pedido'
import type {
  Atendimento,
  MotivoDenuncia,
  Pedido,
  PedidoContato,
  StatusPedido,
} from '../types/api'

// Import dinâmico: o Leaflet acessa `window` ao carregar e não monta bem em
// jsdom. O mini-mapa é mockado nos testes; aqui carregamos sob demanda.
const MapaPedidos = lazy(() => import('../components/MapaPedidos'))

const TIPOS_AJUDA = [
  { value: 'racao', label: 'Ração' },
  { value: 'transporte', label: 'Transporte' },
  { value: 'veterinario', label: 'Veterinário' },
  { value: 'lar_temporario', label: 'Lar temporário' },
  { value: 'resgate', label: 'Resgate' },
]

/**
 * Página de detalhe de um pedido (`/pedidos/:pedidoId`).
 *
 * Exibe galeria de imagens reais (com fallback ilustrado), badges de
 * categoria/urgência/status/espécie/porte/localização, mini-mapa quando há
 * coordenadas, ações de compartilhar e revelar contato (login obrigatório),
 * fluxo "Quero ajudar" (login obrigatório, sem `doador_id`), ações de autor
 * (editar/excluir/mudar status), denúncia e histórico de atendimentos.
 *
 * @returns Tela de detalhe integrada à API.
 */
export function PedidoDetalhePage() {
  const { pedidoId } = useParams()
  const numericPedidoId = Number(pedidoId)
  const pedidoIdValido = Number.isInteger(numericPedidoId) && numericPedidoId > 0
  const navigate = useNavigate()
  const { mostrar } = useToast()
  const { usuario, isAuthenticated } = useAuth()

  const [pedido, setPedido] = useState<Pedido | null>(null)
  const [atendimentos, setAtendimentos] = useState<Atendimento[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [contato, setContato] = useState<PedidoContato | null>(null)
  const [revelandoContato, setRevelandoContato] = useState(false)
  const [mostrandoAjuda, setMostrandoAjuda] = useState(false)
  const [confirmandoExclusao, setConfirmandoExclusao] = useState(false)
  const [denunciando, setDenunciando] = useState(false)

  useEffect(() => {
    let active = true
    if (!pedidoIdValido) {
      setPedido(null)
      setAtendimentos([])
      setError('Pedido não encontrado.')
      setLoading(false)
      return () => {
        active = false
      }
    }
    setLoading(true)
    setError(null)
    Promise.all([obterPedido(numericPedidoId), listarAtendimentos(numericPedidoId)])
      .then(([pedidoResponse, atendimentosResponse]) => {
        if (active) {
          setPedido(pedidoResponse)
          setAtendimentos(atendimentosResponse)
          setLoading(false)
        }
      })
      .catch(() => {
        if (active) {
          setError('Não foi possível carregar este pedido.')
          setLoading(false)
        }
      })
    return () => {
      active = false
    }
  }, [numericPedidoId, pedidoIdValido])

  async function handleRevelarContato() {
    setRevelandoContato(true)
    try {
      const dados = await revelarContato(numericPedidoId)
      setContato(dados)
    } catch {
      mostrar('Não foi possível revelar o contato. Tente novamente.', 'erro')
    } finally {
      setRevelandoContato(false)
    }
  }

  async function handleCompartilhar() {
    const url = window.location.href
    const titulo = pedido?.titulo ?? 'Pedido de ajuda'
    if (navigator.share) {
      try {
        await navigator.share({ title: titulo, url })
        return
      } catch {
        // Compartilhamento cancelado pelo usuário: segue para o fallback.
      }
    }
    if (navigator.clipboard) {
      try {
        await navigator.clipboard.writeText(url)
        mostrar('Link copiado para a área de transferência.', 'sucesso')
        return
      } catch {
        // Sem permissão de clipboard: cai no fallback do WhatsApp.
      }
    }
    window.open(`https://wa.me/?text=${encodeURIComponent(`${titulo} ${url}`)}`, '_blank')
  }

  async function handleAjuda(payload: { tipo_ajuda: string; observacao?: string }) {
    const atendimento = await criarAtendimento(numericPedidoId, payload)
    setAtendimentos((current) => [...current, atendimento])
    setMostrandoAjuda(false)
    mostrar('Ajuda registrada. Obrigado por apoiar este pedido!', 'sucesso')
  }

  async function handleMudarStatus(novoStatus: StatusPedido) {
    try {
      const atualizado = await alterarStatusPedido(numericPedidoId, novoStatus)
      setPedido(atualizado)
      mostrar('Status atualizado.', 'sucesso')
    } catch {
      mostrar('Não foi possível atualizar o status.', 'erro')
    }
  }

  async function handleExcluir() {
    try {
      await excluirPedido(numericPedidoId)
      setConfirmandoExclusao(false)
      mostrar('Pedido excluído.', 'sucesso')
      navigate('/pedidos')
    } catch {
      mostrar('Não foi possível excluir o pedido.', 'erro')
    }
  }

  async function handleDenunciar(payload: { motivo: MotivoDenuncia; descricao?: string }) {
    await denunciarPedido(numericPedidoId, payload)
    setDenunciando(false)
    mostrar('Denúncia enviada. Obrigado por ajudar a manter a rede segura.', 'sucesso')
  }

  if (loading) {
    return (
      <section className="rsp-page">
        <div className="rsp-skeleton" role="status">
          Carregando pedido...
        </div>
      </section>
    )
  }

  if (error || !pedido) {
    return (
      <section className="rsp-page">
        <div className="rsp-empty">{error ?? 'Pedido não encontrado.'}</div>
      </section>
    )
  }

  const ehAutor =
    isAuthenticated &&
    usuario !== null &&
    (pedido.autor_id === usuario.id || usuario.papel === 'admin')
  const localizacao = rotuloLocalizacao(pedido)
  const imagens = [...(pedido.imagens ?? [])].sort((a, b) => a.ordem - b.ordem)
  const podeAjudar = pedido.status === 'aberto' || pedido.status === 'em_andamento'

  return (
    <section className="rsp-page rsp-detail">
      <Seo title={pedido.titulo} description={pedido.descricao.slice(0, 160)} />
      <Link className="rsp-textlink" to="/pedidos">
        Voltar aos pedidos
      </Link>
      <div className="rsp-detail__layout">
        <div className="rsp-detail__main">
          <Galeria titulo={pedido.titulo} imagens={imagens} />

          <div className="rsp-meta-row" aria-label="Características do pedido" role="group">
            <Badge tone={tomUrgencia(pedido.urgencia)}>{rotuloDe(urgencias, pedido.urgencia)}</Badge>
            <Badge tone="neutral">{rotuloDe(statusOpcoes, pedido.status)}</Badge>
            <Badge tone="neutral">{rotuloDe(categorias, pedido.categoria)}</Badge>
            {pedido.especie && <Badge tone="neutral">{rotuloDe(especies, pedido.especie)}</Badge>}
            {pedido.porte && <Badge tone="neutral">{rotuloDe(portes, pedido.porte)}</Badge>}
            {pedido.sexo && <Badge tone="neutral">{rotuloDe(sexos, pedido.sexo)}</Badge>}
            {localizacao && <Badge tone="neutral">{localizacao}</Badge>}
          </div>

          <h1 className="rsp-detail-title">{pedido.titulo}</h1>
          <p className="rsp-prose">{pedido.descricao}</p>

          {temCoordenadas(pedido) && (
            <section className="rsp-detail__section" aria-labelledby="mapa-title">
              <h2 id="mapa-title" className="rsp-block-label">
                Localização aproximada
              </h2>
              <Suspense fallback={<div className="rsp-skeleton">Carregando mapa...</div>}>
                <MapaPedidos
                  centro={[pedido.latitude, pedido.longitude]}
                  zoom={14}
                  pontos={[
                    {
                      id: pedido.id,
                      titulo: pedido.titulo,
                      latitude: pedido.latitude,
                      longitude: pedido.longitude,
                    },
                  ]}
                />
              </Suspense>
            </section>
          )}

          <section className="rsp-detail__section" aria-labelledby="historico-title">
            <h2 id="historico-title" className="rsp-block-label">
              Histórico de atendimentos
            </h2>
            {atendimentos.length === 0 ? (
              <p className="rsp-empty">Nenhuma ajuda registrada ainda.</p>
            ) : (
              <ul className="rsp-stack rsp-historico">
                {atendimentos.map((atendimento) => (
                  <li className="rsp-card" key={atendimento.id}>
                    <div className="rsp-historico__head">
                      <strong>{rotuloDe(TIPOS_AJUDA, atendimento.tipo_ajuda)}</strong>
                      <time dateTime={atendimento.data_contato}>
                        {new Date(atendimento.data_contato).toLocaleDateString('pt-BR')}
                      </time>
                    </div>
                    {atendimento.observacao && <p>{atendimento.observacao}</p>}
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>

        <aside className="rsp-detail__aside">
          <div className="rsp-card rsp-detail__aside-card">
            <p className="rsp-block-label">Contato do responsável</p>
            {contato ? (
              <RevelacaoContato contato={contato} />
            ) : isAuthenticated ? (
              <Button
                variant="secondary"
                onClick={handleRevelarContato}
                disabled={revelandoContato}
              >
                {revelandoContato ? 'Carregando...' : 'Revelar contato'}
              </Button>
            ) : (
              <Link className="rsp-btn rsp-btn--secondary rsp-btn--block" to="/entrar">
                Entrar para ver o contato
              </Link>
            )}
            <p className="rsp-help">
              Por privacidade, o contato só aparece após login e clique explícito.
            </p>

            <Button variant="secondary" className="rsp-btn--block" onClick={handleCompartilhar}>
              Compartilhar
            </Button>

            {podeAjudar &&
              (isAuthenticated ? (
                <Button className="rsp-btn--block" onClick={() => setMostrandoAjuda((v) => !v)}>
                  Quero ajudar
                </Button>
              ) : (
                <Link className="rsp-btn rsp-btn--primary rsp-btn--block" to="/entrar">
                  Entrar para ajudar
                </Link>
              ))}

            {mostrandoAjuda && isAuthenticated && <FormularioAjuda onSubmit={handleAjuda} />}

            {isAuthenticated && (
              <Button
                variant="ghost"
                className="rsp-btn--block"
                onClick={() => setDenunciando(true)}
              >
                Denunciar
              </Button>
            )}
          </div>

          {ehAutor && (
            <div className="rsp-card rsp-detail__aside-card">
              <p className="rsp-block-label">Ações do autor</p>
              <Link
                className="rsp-btn rsp-btn--secondary rsp-btn--block"
                to={`/pedidos/${pedido.id}/editar`}
              >
                Editar
              </Link>
              {pedido.status !== 'concluido' && (
                <Button
                  variant="secondary"
                  className="rsp-btn--block"
                  onClick={() => handleMudarStatus('concluido')}
                >
                  Marcar como concluído
                </Button>
              )}
              {pedido.status !== 'cancelado' && pedido.status !== 'concluido' && (
                <Button
                  variant="secondary"
                  className="rsp-btn--block"
                  onClick={() => handleMudarStatus('cancelado')}
                >
                  Cancelar pedido
                </Button>
              )}
              <Button
                variant="ghost"
                className="rsp-btn--block rsp-btn--danger"
                onClick={() => setConfirmandoExclusao(true)}
              >
                Excluir
              </Button>
            </div>
          )}
        </aside>
      </div>

      <Modal
        open={confirmandoExclusao}
        onClose={() => setConfirmandoExclusao(false)}
        titulo="Excluir pedido"
        rodape={
          <>
            <Button variant="secondary" onClick={() => setConfirmandoExclusao(false)}>
              Cancelar
            </Button>
            <Button className="rsp-btn--danger" onClick={handleExcluir}>
              Confirmar exclusão
            </Button>
          </>
        }
      >
        <p>
          Tem certeza de que deseja excluir <strong>{pedido.titulo}</strong>? Esta ação não pode
          ser desfeita.
        </p>
      </Modal>

      <ModalDenuncia
        open={denunciando}
        onClose={() => setDenunciando(false)}
        onSubmit={handleDenunciar}
      />
    </section>
  )
}

type GaleriaProps = {
  titulo: string
  imagens: { id: number; url: string; ordem: number }[]
}

/**
 * Galeria de imagens reais do pedido, com fallback ilustrado quando sem fotos.
 *
 * @param props - Título (usado no `alt`) e imagens ordenadas.
 * @returns Bloco de imagem destaque mais miniaturas, ou um placeholder.
 */
function Galeria({ titulo, imagens }: GaleriaProps) {
  const [ativa, setAtiva] = useState(0)

  if (imagens.length === 0) {
    return (
      <div className="rsp-detail__hero rsp-detail__hero--vazio" role="img" aria-label="Sem foto disponível">
        <span aria-hidden="true">🐾</span>
        <span className="rsp-help">Sem foto disponível</span>
      </div>
    )
  }

  const destaque = imagens[Math.min(ativa, imagens.length - 1)]

  return (
    <div className="rsp-galeria">
      <img
        className="rsp-galeria__destaque"
        src={destaque.url}
        alt={`Foto de ${titulo}`}
        loading="lazy"
      />
      {imagens.length > 1 && (
        <div className="rsp-galeria__thumbs">
          {imagens.map((imagem, indice) => (
            <button
              key={imagem.id}
              type="button"
              className={`rsp-galeria__thumb ${indice === ativa ? 'is-ativa' : ''}`.trim()}
              aria-label={`Ver foto ${indice + 1}`}
              aria-pressed={indice === ativa}
              onClick={() => setAtiva(indice)}
            >
              <img src={imagem.url} alt="" loading="lazy" />
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

type RevelacaoContatoProps = {
  contato: PedidoContato
}

/**
 * Bloco de contato revelado com botão de WhatsApp quando disponível.
 *
 * @param props - Contato e link de WhatsApp retornados pela API.
 * @returns Texto do contato e, se houver, ação para abrir o WhatsApp.
 */
function RevelacaoContato({ contato }: RevelacaoContatoProps) {
  return (
    <div className="rsp-contato">
      <p className="rsp-contato__value">{contato.contato}</p>
      {contato.whatsapp && (
        <a
          className="rsp-btn rsp-btn--secondary rsp-btn--block"
          href={contato.whatsapp}
          target="_blank"
          rel="noreferrer"
        >
          Abrir no WhatsApp
        </a>
      )}
    </div>
  )
}

type FormularioAjudaProps = {
  onSubmit: (payload: { tipo_ajuda: string; observacao?: string }) => Promise<void>
}

/**
 * Formulário "Quero ajudar": registra um atendimento sem expor o doador.
 *
 * @param props - Callback de envio que recebe `{tipo_ajuda, observacao?}`.
 * @returns Formulário com seletor de tipo de ajuda e observação opcional.
 */
function FormularioAjuda({ onSubmit }: FormularioAjudaProps) {
  const [tipoAjuda, setTipoAjuda] = useState('transporte')
  const [observacao, setObservacao] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setEnviando(true)
    setErro(null)
    try {
      const payload: { tipo_ajuda: string; observacao?: string } = { tipo_ajuda: tipoAjuda }
      const texto = observacao.trim()
      if (texto) {
        payload.observacao = texto
      }
      await onSubmit(payload)
    } catch {
      setErro('Não foi possível registrar sua ajuda. Tente novamente.')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <form className="rsp-help-form" onSubmit={handleSubmit}>
      {erro && (
        <p role="alert" className="rsp-alert">
          {erro}
        </p>
      )}
      <Select
        id="tipo-ajuda"
        label="Tipo de ajuda"
        value={tipoAjuda}
        onChange={(event) => setTipoAjuda(event.target.value)}
        options={TIPOS_AJUDA}
      />
      <label className="rsp-field" htmlFor="observacao-ajuda">
        <span>Observação</span>
        <textarea
          id="observacao-ajuda"
          className="rsp-input rsp-textarea"
          value={observacao}
          onChange={(event) => setObservacao(event.target.value)}
          placeholder="Como você pode ajudar? (opcional)"
        />
      </label>
      <p className="rsp-help">
        Ao confirmar, seus dados de contato ficam visíveis apenas para o autor do pedido.
      </p>
      <Button type="submit" disabled={enviando}>
        {enviando ? 'Confirmando...' : 'Confirmar ajuda'}
      </Button>
    </form>
  )
}

type ModalDenunciaProps = {
  open: boolean
  onClose: () => void
  onSubmit: (payload: { motivo: MotivoDenuncia; descricao?: string }) => Promise<void>
}

/**
 * Modal de denúncia com motivo obrigatório e descrição opcional.
 *
 * @param props - Estado de abertura, fechamento e envio da denúncia.
 * @returns Diálogo acessível para enviar uma denúncia.
 */
function ModalDenuncia({ open, onClose, onSubmit }: ModalDenunciaProps) {
  const [motivo, setMotivo] = useState<MotivoDenuncia>('spam')
  const [descricao, setDescricao] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  async function handleSubmit() {
    setEnviando(true)
    setErro(null)
    try {
      const payload: { motivo: MotivoDenuncia; descricao?: string } = { motivo }
      const texto = descricao.trim()
      if (texto) {
        payload.descricao = texto
      }
      await onSubmit(payload)
    } catch {
      setErro('Não foi possível enviar a denúncia. Tente novamente.')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      titulo="Denunciar pedido"
      rodape={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
          <Button onClick={handleSubmit} disabled={enviando}>
            {enviando ? 'Enviando...' : 'Enviar denúncia'}
          </Button>
        </>
      }
    >
      {erro && (
        <p role="alert" className="rsp-alert">
          {erro}
        </p>
      )}
      <Select
        id="motivo-denuncia"
        label="Motivo"
        value={motivo}
        onChange={(event) => setMotivo(event.target.value as MotivoDenuncia)}
        options={motivosDenuncia}
      />
      <label className="rsp-field" htmlFor="descricao-denuncia">
        <span>Descrição (opcional)</span>
        <textarea
          id="descricao-denuncia"
          className="rsp-input rsp-textarea"
          value={descricao}
          onChange={(event) => setDescricao(event.target.value)}
          placeholder="Conte o que está errado neste pedido."
        />
      </label>
    </Modal>
  )
}
