import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HelmetProvider } from 'react-helmet-async'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { PedidoEditarPage } from './PedidoEditarPage'
import { editarPedido, obterPedido } from '../services/api/pedidos'
import type { Pedido, UsuarioRead } from '../types/api'

vi.mock('../services/api/pedidos', () => ({
  obterPedido: vi.fn(),
  editarPedido: vi.fn(),
}))

let authState: { usuario: UsuarioRead | null }
vi.mock('../auth/AuthContext', () => ({
  useAuth: () => authState,
}))

const mostrarMock = vi.fn()
vi.mock('../components/Toast', () => ({
  useToast: () => ({ mostrar: mostrarMock }),
}))

const autor: UsuarioRead = { id: 1, nome: 'Ana', email: 'ana@x.com', papel: 'protetor' }

const pedido: Pedido = {
  id: 7,
  titulo: 'Gata precisa de transporte',
  descricao: 'Precisa ir até a clínica parceira para consulta.',
  categoria: 'transporte',
  urgencia: 'alta',
  status: 'aberto',
  data_criacao: '2026-05-27T12:00:00Z',
  cidade: 'São Paulo',
  estado: 'SP',
  autor_id: 1,
}

describe('PedidoEditarPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    authState = { usuario: autor }
    vi.mocked(obterPedido).mockResolvedValue(pedido)
    vi.mocked(editarPedido).mockResolvedValue({ ...pedido, titulo: 'Gata adotada' })
  })

  function renderPage() {
    render(
      <HelmetProvider>
        <MemoryRouter initialEntries={['/pedidos/7/editar']}>
          <Routes>
            <Route path="/pedidos/:pedidoId/editar" element={<PedidoEditarPage />} />
            <Route path="/pedidos/:pedidoId" element={<div>Detalhe do pedido</div>} />
          </Routes>
        </MemoryRouter>
      </HelmetProvider>,
    )
  }

  it('carrega o pedido e popula o formulário', async () => {
    renderPage()

    expect(await screen.findByDisplayValue('Gata precisa de transporte')).toBeInTheDocument()
    expect(screen.getByLabelText('Categoria')).toHaveValue('transporte')
    expect(screen.getByLabelText('Estado')).toHaveValue('SP')
  })

  it('salva via PATCH e navega ao detalhe', async () => {
    const user = userEvent.setup()
    renderPage()
    const titulo = await screen.findByDisplayValue('Gata precisa de transporte')

    await user.clear(titulo)
    await user.type(titulo, 'Gata adotada com sucesso')
    await user.click(screen.getByRole('button', { name: /salvar alterações/i }))

    await waitFor(() =>
      expect(editarPedido).toHaveBeenCalledWith(
        7,
        expect.objectContaining({ titulo: 'Gata adotada com sucesso', categoria: 'transporte' }),
      ),
    )
    expect(await screen.findByText('Detalhe do pedido')).toBeInTheDocument()
  })

  it('mostra mensagem amigável em 404', async () => {
    vi.mocked(obterPedido).mockRejectedValue({ response: { status: 404 } })
    renderPage()

    expect(await screen.findByText(/pedido não encontrado/i)).toBeInTheDocument()
  })

  it('mostra mensagem amigável em 403', async () => {
    vi.mocked(obterPedido).mockRejectedValue({ response: { status: 403 } })
    renderPage()

    expect(await screen.findByText(/não tem permissão/i)).toBeInTheDocument()
  })
})
