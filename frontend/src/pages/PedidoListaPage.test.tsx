import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HelmetProvider } from 'react-helmet-async'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { PedidoListaPage } from './PedidoListaPage'
import { listarPedidos } from '../services/api/pedidos'
import type { PedidoPage } from '../types/api'

vi.mock('../services/api/pedidos', () => ({
  listarPedidos: vi.fn(),
}))

const pedidoPage: PedidoPage = {
  items: [
    {
      id: 7,
      titulo: 'Gata precisa de transporte',
      descricao: 'Precisa ir até a clínica parceira para consulta.',
      categoria: 'transporte',
      urgencia: 'alta',
      status: 'aberto',
      data_criacao: '2026-05-27T12:00:00',
      cidade: 'São Paulo',
      estado: 'SP',
      total_atendimentos: 2,
      imagens: [{ id: 1, url: '/uploads/gata.jpg', ordem: 0 }],
    },
  ],
  page_info: { page: 1, page_size: 20, total: 1, total_pages: 1 },
}

describe('PedidoListaPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(listarPedidos).mockResolvedValue(pedidoPage)
  })

  function renderPage(path = '/pedidos?urgencia=alta&q=gata') {
    render(
      <HelmetProvider>
        <MemoryRouter initialEntries={[path]}>
          <Routes>
            <Route path="/pedidos" element={<PedidoListaPage />} />
          </Routes>
        </MemoryRouter>
      </HelmetProvider>,
    )
  }

  it('carrega pedidos usando filtros da URL e renderiza cards com thumbnail e localização', async () => {
    renderPage()

    await waitFor(() =>
      expect(listarPedidos).toHaveBeenCalledWith({
        page: 1,
        page_size: 20,
        q: 'gata',
        urgencia: 'alta',
      }),
    )
    const card = await screen.findByRole('link', { name: /gata precisa de transporte/i })
    expect(card).toHaveAttribute('href', '/pedidos/7')
    expect(screen.getByText('Urgente')).toBeInTheDocument()
    expect(screen.getByText('São Paulo, SP')).toBeInTheDocument()
    expect(within(card).getByRole('img')).toHaveAttribute('src', '/uploads/gata.jpg')
    expect(screen.getByText(/2 atendimentos/i)).toBeInTheDocument()
  })

  it('mostra esqueletos de carregamento e não a frase "perto de você" sem geolocalização', async () => {
    renderPage('/pedidos')

    expect(screen.getByRole('status')).toBeInTheDocument()
    await screen.findByRole('link', { name: /gata precisa de transporte/i })
    expect(screen.queryByText(/perto de você/i)).not.toBeInTheDocument()
  })

  it('reflete busca e urgência na URL antes de recarregar', async () => {
    const user = userEvent.setup()
    renderPage('/pedidos')

    await user.type(screen.getByLabelText('Buscar pedidos'), 'ração')
    await user.click(screen.getByRole('button', { name: /urgentes/i }))

    expect(await screen.findByDisplayValue('ração')).toBeInTheDocument()
    await waitFor(() =>
      expect(listarPedidos).toHaveBeenLastCalledWith(
        expect.objectContaining({ q: 'ração', urgencia: 'alta' }),
      ),
    )
  })

  it('carrega categoria, status, cidade e estado vindos da URL', async () => {
    renderPage('/pedidos?categoria=transporte&status=em_andamento&cidade=Campinas&estado=SP&page=2')

    await waitFor(() =>
      expect(listarPedidos).toHaveBeenCalledWith({
        page: 2,
        page_size: 20,
        categoria: 'transporte',
        status: 'em_andamento',
        cidade: 'Campinas',
        estado: 'SP',
      }),
    )
    expect(await screen.findByLabelText('Categoria')).toHaveValue('transporte')
    expect(screen.getByLabelText('Status')).toHaveValue('em_andamento')
    expect(screen.getByLabelText('Estado')).toHaveValue('SP')
    expect(screen.getByLabelText('Cidade')).toHaveValue('Campinas')
  })

  it('reflete espécie, porte e paginação na URL antes de recarregar', async () => {
    const user = userEvent.setup()
    vi.mocked(listarPedidos).mockResolvedValue({
      ...pedidoPage,
      page_info: { page: 1, page_size: 20, total: 42, total_pages: 3 },
    })
    renderPage('/pedidos')

    await user.selectOptions(await screen.findByLabelText('Espécie'), 'gato')
    await user.selectOptions(screen.getByLabelText('Porte'), 'pequeno')
    await user.click(screen.getByRole('button', { name: /próxima página/i }))

    await waitFor(() =>
      expect(listarPedidos).toHaveBeenLastCalledWith(
        expect.objectContaining({ page: 2, especie: 'gato', porte: 'pequeno' }),
      ),
    )
  })
})
