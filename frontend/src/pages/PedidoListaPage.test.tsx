import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
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
      contato: '11999990000',
      data_criacao: '2026-05-27T12:00:00',
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
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/pedidos" element={<PedidoListaPage />} />
        </Routes>
      </MemoryRouter>,
    )
  }

  it('carrega pedidos usando filtros da URL e renderiza cards', async () => {
    renderPage()

    await waitFor(() =>
      expect(listarPedidos).toHaveBeenCalledWith({
        page: 1,
        page_size: 20,
        q: 'gata',
        urgencia: 'alta',
      }),
    )
    expect(await screen.findByRole('link', { name: /gata precisa de transporte/i })).toHaveAttribute(
      'href',
      '/pedidos/7',
    )
    expect(screen.getByText('Urgente')).toBeInTheDocument()
  })

  it('reflete busca e urgência na URL antes de recarregar', async () => {
    const user = userEvent.setup()
    renderPage('/pedidos')

    await user.type(screen.getByLabelText('Buscar pedidos'), 'ração')
    await user.click(screen.getByRole('button', { name: /urgentes/i }))

    expect(await screen.findByDisplayValue('ração')).toBeInTheDocument()
    await waitFor(() => expect(listarPedidos).toHaveBeenLastCalledWith(expect.objectContaining({
      q: 'ração',
      urgencia: 'alta',
    })))
  })

  it('carrega categoria, status e página vindos da URL', async () => {
    renderPage('/pedidos?categoria=transporte&status=em_andamento&page=2')

    await waitFor(() =>
      expect(listarPedidos).toHaveBeenCalledWith({
        page: 2,
        page_size: 20,
        categoria: 'transporte',
        status: 'em_andamento',
      }),
    )
    expect(await screen.findByLabelText('Categoria')).toHaveValue('transporte')
    expect(screen.getByLabelText('Status')).toHaveValue('em_andamento')
  })

  it('reflete categoria, status e paginação na URL antes de recarregar', async () => {
    const user = userEvent.setup()
    vi.mocked(listarPedidos).mockResolvedValue({
      ...pedidoPage,
      page_info: { page: 1, page_size: 20, total: 42, total_pages: 3 },
    })
    renderPage('/pedidos')

    await user.selectOptions(await screen.findByLabelText('Categoria'), 'ração')
    await user.selectOptions(screen.getByLabelText('Status'), 'em_andamento')
    await user.click(screen.getByRole('button', { name: /próxima página/i }))

    await waitFor(() =>
      expect(listarPedidos).toHaveBeenLastCalledWith(expect.objectContaining({
        page: 2,
        categoria: 'ração',
        status: 'em_andamento',
      })),
    )
  })
})
