import { render, screen, waitFor } from '@testing-library/react'
import { HelmetProvider } from 'react-helmet-async'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { MapaPage } from './MapaPage'
import { listarPedidos } from '../services/api/pedidos'
import type { PedidoPage } from '../types/api'

vi.mock('../services/api/pedidos', () => ({
  listarPedidos: vi.fn(),
}))

// O mapa Leaflet não monta em jsdom: mocamos por um marcador estático que
// expõe a contagem de pontos recebidos.
vi.mock('../components/MapaPedidos', () => ({
  __esModule: true,
  default: ({ pontos }: { pontos: { id: number }[] }) => (
    <div data-testid="mock-mapa">mapa com {pontos.length} ponto(s)</div>
  ),
}))

const pagina: PedidoPage = {
  items: [
    {
      id: 7,
      titulo: 'Com coordenadas',
      descricao: 'x',
      categoria: 'transporte',
      urgencia: 'alta',
      status: 'aberto',
      data_criacao: '2026-05-27T12:00:00Z',
      latitude: -23.5,
      longitude: -46.6,
    },
    {
      id: 8,
      titulo: 'Sem coordenadas',
      descricao: 'x',
      categoria: 'racao',
      urgencia: 'baixa',
      status: 'aberto',
      data_criacao: '2026-05-27T12:00:00Z',
    },
  ],
  page_info: { page: 1, page_size: 100, total: 2, total_pages: 1 },
}

describe('MapaPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(listarPedidos).mockResolvedValue(pagina)
  })

  it('renderiza apenas os pedidos com coordenadas como pontos', async () => {
    render(
      <HelmetProvider>
        <MemoryRouter>
          <MapaPage />
        </MemoryRouter>
      </HelmetProvider>,
    )

    await waitFor(() => expect(screen.getByTestId('mock-mapa')).toBeInTheDocument())
    expect(screen.getByTestId('mock-mapa')).toHaveTextContent('mapa com 1 ponto(s)')
    expect(screen.getByText(/1 pedido com localização no mapa/i)).toBeInTheDocument()
  })
})
