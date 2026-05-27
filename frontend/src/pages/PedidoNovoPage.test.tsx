import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { PedidoNovoPage } from './PedidoNovoPage'
import { criarPedido } from '../services/api/pedidos'

vi.mock('../services/api/pedidos', () => ({
  criarPedido: vi.fn(),
}))

const pedidoCriado = {
  id: 22,
  titulo: 'Ração para filhotes',
  descricao: 'Família temporária precisa de ração hoje.',
  categoria: 'ração',
  urgencia: 'alta' as const,
  status: 'aberto' as const,
  contato: '11999990000',
  data_criacao: '2026-05-27T12:00:00',
}

describe('PedidoNovoPage', () => {
  beforeEach(() => {
    vi.mocked(criarPedido).mockResolvedValue(pedidoCriado)
  })

  function renderPage() {
    render(
      <MemoryRouter initialEntries={['/pedidos/novo']}>
        <Routes>
          <Route path="/pedidos/novo" element={<PedidoNovoPage />} />
          <Route path="/pedidos/:pedidoId" element={<h1>Detalhe criado</h1>} />
        </Routes>
      </MemoryRouter>,
    )
  }

  it('mostra validações em PT-BR para envio vazio', async () => {
    const user = userEvent.setup()
    renderPage()

    await user.click(screen.getByRole('button', { name: /publicar pedido/i }))

    expect(screen.getByText('Informe um título com pelo menos 3 caracteres.')).toBeInTheDocument()
    expect(screen.getByText('Informe uma descrição com pelo menos 10 caracteres.')).toBeInTheDocument()
    expect(criarPedido).not.toHaveBeenCalled()
  })

  it('envia payload válido e navega para o detalhe criado', async () => {
    const user = userEvent.setup()
    renderPage()

    await user.type(screen.getByLabelText('Título do pedido'), 'Ração para filhotes')
    await user.selectOptions(screen.getByLabelText('Categoria'), 'ração')
    await user.selectOptions(screen.getByLabelText('Urgência'), 'alta')
    await user.type(
      screen.getByLabelText('Descrição'),
      'Família temporária precisa de ração hoje.',
    )
    await user.type(screen.getByLabelText('Contato'), '11999990000')
    await user.click(screen.getByRole('button', { name: /publicar pedido/i }))

    await waitFor(() =>
      expect(criarPedido).toHaveBeenCalledWith({
        titulo: 'Ração para filhotes',
        categoria: 'ração',
        urgencia: 'alta',
        descricao: 'Família temporária precisa de ração hoje.',
        contato: '11999990000',
      }),
    )
    expect(await screen.findByRole('heading', { name: 'Detalhe criado' })).toBeInTheDocument()
  })
})
