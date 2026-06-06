import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { Button, Select, Skeleton } from '../components/ui'
import { Seo } from '../components/Seo'
import {
  categorias,
  especies,
  portes,
  rotuloDe,
  status as statusOpcoes,
  ufs,
  urgencias,
} from '../constants/dominio'
import { listarPedidos, type PedidoListParams } from '../services/api/pedidos'
import { rotuloLocalizacao, tomUrgencia, urlCapa } from '../utils/pedido'
import type { Especie, Pedido, PedidoPage, Porte, StatusPedido, Urgencia } from '../types/api'

const PAGE_SIZE = 20

/** Adiciona uma opção placeholder vazia no topo de uma lista de domínio. */
function comTodos(opcoes: { value: string; label: string }[], texto: string) {
  return [{ value: '', label: texto }, ...opcoes]
}

/**
 * Página de lista pública de pedidos com busca textual e filtros reais.
 *
 * Todos os filtros (busca, urgência, categoria, status, espécie, porte, cidade
 * e estado) são refletidos na URL para serem compartilháveis e recarregáveis.
 * Exibe esqueletos com shimmer durante o carregamento e cards com a foto de
 * capa real (ou fallback), localização e contagem de atendimentos.
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
  const especie = searchParams.get('especie') ?? ''
  const porte = searchParams.get('porte') ?? ''
  const cidade = searchParams.get('cidade') ?? ''
  const estado = searchParams.get('estado') ?? ''
  const page = Math.max(Number(searchParams.get('page') ?? '1') || 1, 1)

  // Campo de cidade é controlado localmente e só vira filtro de URL ao submeter,
  // evitando uma chamada à API a cada tecla digitada.
  const [cidadeInput, setCidadeInput] = useState(cidade)
  useEffect(() => {
    setCidadeInput(cidade)
  }, [cidade])

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)
    const params: PedidoListParams = {
      page,
      page_size: PAGE_SIZE,
      ...(q ? { q } : {}),
      ...(urgencia ? { urgencia } : {}),
      ...(categoria ? { categoria } : {}),
      ...(status ? { status } : {}),
      ...(especie ? { especie } : {}),
      ...(porte ? { porte } : {}),
      ...(cidade ? { cidade } : {}),
      ...(estado ? { estado } : {}),
    }
    listarPedidos(params)
      .then((resposta) => {
        if (active) {
          setPedidoPage(resposta)
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
  }, [categoria, cidade, especie, estado, page, porte, q, status, urgencia])

  const total = pedidoPage?.page_info.total ?? 0
  const totalPages = pedidoPage?.page_info.total_pages ?? 1
  const pedidos = useMemo(() => pedidoPage?.items ?? [], [pedidoPage])

  function updateFilter(next: Record<string, string | number | null>) {
    const params = new URLSearchParams(searchParams)
    for (const [chave, valor] of Object.entries(next)) {
      if (chave === 'page') {
        if (typeof valor === 'number' && valor > 1) {
          params.set('page', String(valor))
        } else {
          params.delete('page')
        }
        continue
      }
      const texto = typeof valor === 'string' ? valor.trim() : ''
      if (texto) {
        params.set(chave, texto)
      } else {
        params.delete(chave)
      }
      params.delete('page')
    }
    setSearchParams(params, { replace: true })
  }

  function aplicarCidade(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    updateFilter({ cidade: cidadeInput })
  }

  return (
    <section className="rsp-page rsp-feed">
      <Seo
        title="Pedidos da comunidade"
        description="Veja e filtre pedidos de ajuda para animais em situação de vulnerabilidade."
      />
      <div className="rsp-page__header">
        <div>
          <p className="rsp-eyebrow">Comunidade</p>
          <h1 className="rsp-page__title">Pedidos da comunidade</h1>
          <p className="rsp-page__sub" aria-live="polite">
            {loading
              ? 'Carregando pedidos…'
              : `${total} ${total === 1 ? 'pedido encontrado' : 'pedidos encontrados'}.`}
          </p>
        </div>
        <Link className="rsp-btn rsp-btn--secondary" to="/pedidos/mapa">
          Ver no mapa
        </Link>
      </div>

      <div className="rsp-feed__toolbar">
        <label className="rsp-search">
          <span className="rsp-sr-only">Buscar pedidos</span>
          <span aria-hidden="true">⌕</span>
          <input
            aria-label="Buscar pedidos"
            value={q}
            onChange={(event) => updateFilter({ q: event.target.value })}
            placeholder="Buscar por título ou descrição..."
          />
        </label>

        <div className="rsp-filter-selects">
          <Select
            id="categoria-filtro"
            label="Categoria"
            value={categoria}
            onChange={(event) => updateFilter({ categoria: event.target.value })}
            options={comTodos(categorias, 'Todas as categorias')}
          />
          <Select
            id="status-filtro"
            label="Status"
            value={status ?? ''}
            onChange={(event) => updateFilter({ status: event.target.value })}
            options={comTodos(statusOpcoes, 'Todos os status')}
          />
          <Select
            id="especie-filtro"
            label="Espécie"
            value={especie}
            onChange={(event) => updateFilter({ especie: event.target.value })}
            options={comTodos(especies, 'Todas as espécies')}
          />
          <Select
            id="porte-filtro"
            label="Porte"
            value={porte}
            onChange={(event) => updateFilter({ porte: event.target.value })}
            options={comTodos(portes, 'Todos os portes')}
          />
          <Select
            id="estado-filtro"
            label="Estado"
            value={estado}
            onChange={(event) => updateFilter({ estado: event.target.value })}
            options={comTodos(ufs, 'Todos os estados')}
          />
          <form className="rsp-field-wrap" onSubmit={aplicarCidade} role="search">
            <label className="rsp-field" htmlFor="cidade-filtro">
              <span>Cidade</span>
              <input
                id="cidade-filtro"
                className="rsp-input"
                value={cidadeInput}
                onChange={(event) => setCidadeInput(event.target.value)}
                placeholder="Filtrar por cidade"
              />
            </label>
          </form>
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

      {loading && <Skeleton rotulo="Carregando pedidos…" />}
      {error && (
        <div className="rsp-empty" role="alert">
          {error}
        </div>
      )}
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
            <span className="rsp-pagination__status">
              Página {page} de {totalPages}
            </span>
            <Button
              variant="secondary"
              disabled={page >= totalPages}
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
 * Card público de pedido com foto de capa real, localização e atendimentos.
 *
 * @param props - Pedido exibido no feed.
 * @returns Link-card para a rota de detalhe.
 */
function PedidoCard({ pedido }: PedidoCardProps) {
  const capa = urlCapa(pedido)
  const localizacao = rotuloLocalizacao(pedido)
  const atendimentos = pedido.total_atendimentos
  const especie = pedido.especie as Especie | null | undefined
  const porte = pedido.porte as Porte | null | undefined

  return (
    <Link className="rsp-pedido-card" to={`/pedidos/${pedido.id}`}>
      <div className="rsp-pedido-card__media">
        {capa ? (
          <img src={capa} alt={`Foto de ${pedido.titulo}`} loading="lazy" decoding="async" />
        ) : (
          <span className="rsp-pedido-card__media-fallback" aria-hidden="true">
            🐾
          </span>
        )}
        <span
          className={`rsp-pedido-card__urgency rsp-pedido-card__urgency--${tomUrgencia(
            pedido.urgencia,
          )}`}
        >
          {rotuloDe(urgencias, pedido.urgencia)}
        </span>
        {pedido.status !== 'aberto' && (
          <span className="rsp-pedido-card__status">{rotuloDe(statusOpcoes, pedido.status)}</span>
        )}
      </div>
      <div className="rsp-pedido-card__body">
        <p className="rsp-pedido-card__eyebrow">
          <span>{rotuloDe(categorias, pedido.categoria)}</span>
          {localizacao && (
            <>
              <span aria-hidden="true">·</span>
              <span>{localizacao}</span>
            </>
          )}
        </p>
        <h2 className="rsp-pedido-card__title">{pedido.titulo}</h2>
        <p className="rsp-pedido-card__desc">{pedido.descricao}</p>
        <div className="rsp-pedido-card__footer">
          <div className="rsp-pedido-card__tags">
            {especie && <span className="rsp-pedido-card__tag">{rotuloDe(especies, especie)}</span>}
            {porte && <span className="rsp-pedido-card__tag">{rotuloDe(portes, porte)}</span>}
          </div>
          {typeof atendimentos === 'number' && atendimentos > 0 && (
            <span className="rsp-pedido-card__help">
              {atendimentos} {atendimentos === 1 ? 'atendimento' : 'atendimentos'}
            </span>
          )}
        </div>
      </div>
    </Link>
  )
}
