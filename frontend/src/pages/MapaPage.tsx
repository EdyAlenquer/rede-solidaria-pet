import { lazy, Suspense, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { Seo } from '../components/Seo'
import { rotuloDe, urgencias } from '../constants/dominio'
import { listarPedidos } from '../services/api/pedidos'
import { temCoordenadas } from '../utils/pedido'
import type { Pedido } from '../types/api'
import type { PontoMapa } from '../components/MapaPedidos'

// Import dinâmico: o Leaflet acessa `window` no carregamento e não monta bem em
// jsdom. Carregar sob demanda mantém os testes de rota estáveis.
const MapaPedidos = lazy(() => import('../components/MapaPedidos'))

const PAGE_SIZE = 100

/**
 * Página do mapa de pedidos georreferenciados (`/pedidos/mapa`).
 *
 * Carrega pedidos abertos, filtra os que têm coordenadas e os exibe como
 * marcadores no mapa Leaflet, com popup de título/urgência e link para o
 * detalhe. O mapa é carregado via import dinâmico (só no navegador).
 *
 * @returns Tela do mapa com marcadores reais.
 */
export function MapaPage() {
  const [pedidos, setPedidos] = useState<Pedido[]>([])
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    let ativo = true
    setCarregando(true)
    setErro(null)
    listarPedidos({ page: 1, page_size: PAGE_SIZE })
      .then((resposta) => {
        if (ativo) {
          setPedidos(resposta.items)
          setCarregando(false)
        }
      })
      .catch(() => {
        if (ativo) {
          setErro('Não foi possível carregar os pedidos do mapa.')
          setCarregando(false)
        }
      })
    return () => {
      ativo = false
    }
  }, [])

  const pontos = useMemo<PontoMapa[]>(
    () =>
      pedidos.filter(temCoordenadas).map((pedido) => ({
        id: pedido.id,
        titulo: pedido.titulo,
        latitude: pedido.latitude,
        longitude: pedido.longitude,
        popup: (
          <div className="rsp-mapa-popup">
            <strong>{pedido.titulo}</strong>
            <p>Urgência: {rotuloDe(urgencias, pedido.urgencia)}</p>
            <Link to={`/pedidos/${pedido.id}`}>Ver detalhes</Link>
          </div>
        ),
      })),
    [pedidos],
  )

  return (
    <section className="rsp-page rsp-mapa-page">
      <Seo
        title="Mapa de pedidos"
        description="Veja no mapa os pedidos de ajuda para animais georreferenciados."
      />
      <div className="rsp-page__header">
        <div>
          <p className="rsp-eyebrow">Comunidade</p>
          <h1 className="rsp-page__title">Mapa de pedidos</h1>
          <p className="rsp-page__sub">
            {pontos.length}{' '}
            {pontos.length === 1
              ? 'pedido com localização no mapa'
              : 'pedidos com localização no mapa'}
            .
          </p>
        </div>
        <Link className="rsp-btn rsp-btn--secondary" to="/pedidos">
          Ver em lista
        </Link>
      </div>

      {erro && (
        <div className="rsp-empty" role="alert">
          {erro}
        </div>
      )}

      {!erro && (
        <Suspense fallback={<div className="rsp-skeleton" role="status">Carregando mapa...</div>}>
          {carregando ? (
            <div className="rsp-skeleton" role="status">
              Carregando pedidos...
            </div>
          ) : (
            <MapaPedidos pontos={pontos} />
          )}
        </Suspense>
      )}
    </section>
  )
}
