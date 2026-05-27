import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { Badge, Button, Select } from '../components/ui'
import { listarPedidos } from '../services/api/pedidos'
import type { Pedido, PedidoPage, StatusPedido, Urgencia } from '../types/api'

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
  const categoria = searchParams.get('categoria') ?? ''
  const status = searchParams.get('status') as StatusPedido | null
  const page = Math.max(Number(searchParams.get('page') ?? '1') || 1, 1)

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)
    listarPedidos({
      page,
      page_size: PAGE_SIZE,
      ...(q ? { q } : {}),
      ...(urgencia ? { urgencia } : {}),
      ...(categoria ? { categoria } : {}),
      ...(status ? { status } : {}),
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
  }, [categoria, page, q, status, urgencia])

  const total = pedidoPage?.page_info.total ?? 0
  const pedidos = useMemo(() => pedidoPage?.items ?? [], [pedidoPage])

  function updateFilter(next: {
    categoria?: string | null
    page?: number
    q?: string
    status?: StatusPedido | null
    urgencia?: Urgencia | null
  }) {
    const params = new URLSearchParams(searchParams)
    if ('q' in next) {
      const value = next.q?.trim() ?? ''
      if (value) params.set('q', value)
      else params.delete('q')
      params.delete('page')
    }
    if ('categoria' in next) {
      const value = next.categoria?.trim() ?? ''
      if (value) params.set('categoria', value)
      else params.delete('categoria')
      params.delete('page')
    }
    if ('urgencia' in next) {
      if (next.urgencia) params.set('urgencia', next.urgencia)
      else params.delete('urgencia')
      params.delete('page')
    }
    if ('status' in next) {
      if (next.status) params.set('status', next.status)
      else params.delete('status')
      params.delete('page')
    }
    if ('page' in next) {
      if (next.page && next.page > 1) params.set('page', String(next.page))
      else params.delete('page')
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
            value={q}
            onChange={(event) => updateFilter({ q: event.target.value })}
            placeholder="Buscar por bairro, categoria, palavra-chave..."
          />
        </label>
        <div className="rsp-filter-selects">
          <Select
            id="categoria-filtro"
            label="Categoria"
            value={categoria}
            onChange={(event) => updateFilter({ categoria: event.target.value })}
            options={[
              { label: 'Todas as categorias', value: '' },
              { label: 'Ração', value: 'ração' },
              { label: 'Transporte', value: 'transporte' },
              { label: 'Veterinário', value: 'veterinário' },
              { label: 'Lar temporário', value: 'lar temporário' },
              { label: 'Resgate', value: 'resgate' },
            ]}
          />
          <Select
            id="status-filtro"
            label="Status"
            value={status ?? ''}
            onChange={(event) => updateFilter({ status: event.target.value as StatusPedido | null })}
            options={[
              { label: 'Todos os status', value: '' },
              { label: 'Aberto', value: 'aberto' },
              { label: 'Em andamento', value: 'em_andamento' },
              { label: 'Concluído', value: 'concluido' },
            ]}
          />
        </div>
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
        <>
          <div className="rsp-feed__grid">
            {pedidos.map((pedido) => (
              <PedidoCard key={pedido.id} pedido={pedido} />
            ))}
          </div>
          <div className="rsp-pagination" aria-label="Paginação">
            <Button
              variant="secondary"
              disabled={page <= 1}
              onClick={() => updateFilter({ page: page - 1 })}
            >
              Página anterior
            </Button>
            <span>
              Página {page} de {pedidoPage?.page_info.total_pages ?? 1}
            </span>
            <Button
              variant="secondary"
              disabled={page >= (pedidoPage?.page_info.total_pages ?? 1)}
              onClick={() => updateFilter({ page: page + 1 })}
            >
              Próxima página
            </Button>
          </div>
        </>
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
