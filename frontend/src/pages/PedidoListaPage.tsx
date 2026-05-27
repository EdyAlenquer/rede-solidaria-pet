import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { Badge } from '../components/ui'
import { listarPedidos } from '../services/api/pedidos'
import type { Pedido, PedidoPage, Urgencia } from '../types/api'

const PAGE_SIZE = 20

const urgenciaLabels: Record<Urgencia, string> = {
  alta: 'Urgente',
  media: 'Média',
  baixa: 'Baixa',
}

/**
 * Página de lista pública de pedidos com busca e filtros.
 *
 * @returns Tela de feed de pedidos integrada à API.
 */
export function PedidoListaPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [pedidoPage, setPedidoPage] = useState<PedidoPage | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const q = searchParams.get('q') ?? ''
  const urgencia = searchParams.get('urgencia') as Urgencia | null

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)
    listarPedidos({
      page: 1,
      page_size: PAGE_SIZE,
      ...(q ? { q } : {}),
      ...(urgencia ? { urgencia } : {}),
    })
      .then((page) => {
        if (active) {
          setPedidoPage(page)
          setLoading(false)
        }
      })
      .catch(() => {
        if (active) {
          setError('Não foi possível carregar os pedidos. Tente novamente.')
          setLoading(false)
        }
      })

    return () => {
      active = false
    }
  }, [q, urgencia])

  const total = pedidoPage?.page_info.total ?? 0
  const pedidos = useMemo(() => pedidoPage?.items ?? [], [pedidoPage])

  function updateFilter(next: { q?: string; urgencia?: Urgencia | null }) {
    const params = new URLSearchParams(searchParams)
    if ('q' in next) {
      const value = next.q?.trim() ?? ''
      if (value) params.set('q', value)
      else params.delete('q')
    }
    if ('urgencia' in next) {
      if (next.urgencia) params.set('urgencia', next.urgencia)
      else params.delete('urgencia')
    }
    setSearchParams(params, { replace: true })
  }

  return (
    <section className="rsp-page rsp-feed">
      <div className="rsp-page__header">
        <div>
          <p className="rsp-eyebrow">Comunidade</p>
          <h1 className="rsp-page__title">Pedidos da comunidade</h1>
          <p className="rsp-page__sub">
            {total} {total === 1 ? 'pedido encontrado' : 'pedidos encontrados'} perto de você.
          </p>
        </div>
      </div>

      <div className="rsp-feed__toolbar">
        <label className="rsp-search">
          <span className="rsp-sr-only">Buscar pedidos</span>
          <span aria-hidden="true">⌕</span>
          <input
            aria-label="Buscar pedidos"
            defaultValue={q}
            onChange={(event) => updateFilter({ q: event.target.value })}
            placeholder="Buscar por bairro, categoria, palavra-chave..."
          />
        </label>
        <div className="rsp-filter-row" aria-label="Filtrar por urgência">
          <button
            type="button"
            className="rsp-chip"
            aria-pressed={!urgencia}
            onClick={() => updateFilter({ urgencia: null })}
          >
            Todos
          </button>
          <button
            type="button"
            className="rsp-chip"
            aria-pressed={urgencia === 'alta'}
            onClick={() => updateFilter({ urgencia: 'alta' })}
          >
            Urgentes
          </button>
          <button
            type="button"
            className="rsp-chip"
            aria-pressed={urgencia === 'media'}
            onClick={() => updateFilter({ urgencia: 'media' })}
          >
            Média
          </button>
          <button
            type="button"
            className="rsp-chip"
            aria-pressed={urgencia === 'baixa'}
            onClick={() => updateFilter({ urgencia: 'baixa' })}
          >
            Baixa
          </button>
        </div>
      </div>

      {loading && <div className="rsp-skeleton">Carregando pedidos...</div>}
      {error && <div className="rsp-empty">{error}</div>}
      {!loading && !error && pedidos.length === 0 && (
        <div className="rsp-empty">Nenhum pedido encontrado. Tente outro termo ou filtro.</div>
      )}
      {!loading && !error && pedidos.length > 0 && (
        <div className="rsp-feed__grid">
          {pedidos.map((pedido) => (
            <PedidoCard key={pedido.id} pedido={pedido} />
          ))}
        </div>
      )}
    </section>
  )
}

type PedidoCardProps = {
  pedido: Pedido
}

/**
 * Card público de pedido baseado no layout de referência.
 *
 * @param props - Pedido exibido no feed.
 * @returns Link-card para a rota de detalhe.
 */
function PedidoCard({ pedido }: PedidoCardProps) {
  return (
    <Link className="rsp-pedido-card" to={`/pedidos/${pedido.id}`}>
      <div className="rsp-pedido-card__head">
        <div className="rsp-pedido-thumb" aria-hidden="true">
          foto
        </div>
        <div className="rsp-pedido-card__body">
          <h2 className="rsp-pedido-card__title">{pedido.titulo}</h2>
          <p className="rsp-pedido-card__meta">
            {pedido.categoria} · publicado em {new Date(pedido.data_criacao).toLocaleDateString('pt-BR')}
          </p>
        </div>
      </div>
      <p className="rsp-pedido-card__desc">{pedido.descricao}</p>
      <div className="rsp-pedido-card__footer">
        <Badge tone={pedido.urgencia === 'alta' ? 'danger' : pedido.urgencia === 'media' ? 'warning' : 'success'}>
          {urgenciaLabels[pedido.urgencia]}
        </Badge>
        {pedido.status !== 'aberto' && <Badge tone="neutral">{pedido.status.replace('_', ' ')}</Badge>}
      </div>
    </Link>
  )
}
