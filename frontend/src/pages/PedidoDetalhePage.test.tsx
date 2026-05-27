import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { PedidoDetalhePage } from './PedidoDetalhePage'
import { criarAtendimento, listarAtendimentos } from '../services/api/atendimentos'
import { criarDoador } from '../services/api/doadores'
import { obterPedido } from '../services/api/pedidos'

vi.mock('../services/api/atendimentos', () => ({
  criarAtendimento: vi.fn(),
  listarAtendimentos: vi.fn(),
}))

vi.mock('../services/api/doadores', () => ({
  criarDoador: vi.fn(),
}))

vi.mock('../services/api/pedidos', () => ({
  obterPedido: vi.fn(),
}))

const pedido = {
  id: 7,
  titulo: 'Gata precisa de transporte',
  descricao: 'Precisa ir até a clínica parceira para consulta.',
  categoria: 'transporte',
  urgencia: 'alta' as const,
  status: 'aberto' as const,
  contato: '11999990000',
  data_criacao: '2026-05-27T12:00:00',
}

describe('PedidoDetalhePage', () => {
  beforeEach(() => {
    vi.mocked(obterPedido).mockResolvedValue(pedido)
    vi.mocked(listarAtendimentos).mockResolvedValue([
      {
        id: 3,
        pedido_id: 7,
        tipo_ajuda: 'transporte',
        observacao: 'Posso levar amanhã cedo.',
        data_contato: '2026-05-27T13:00:00',
      },
    ])
    vi.mocked(criarDoador).mockResolvedValue({
      id: 11,
      nome: 'Maria',
      telefone: '11988887777',
      email: null,
    })
    vi.mocked(criarAtendimento).mockResolvedValue({
      id: 12,
      pedido_id: 7,
      tipo_ajuda: 'ração',
      observacao: 'Consigo entregar hoje.',
      data_contato: '2026-05-27T14:00:00',
    })
  })

  function renderPage() {
    render(
      <MemoryRouter initialEntries={['/pedidos/7']}>
        <Routes>
          <Route path="/pedidos/:pedidoId" element={<PedidoDetalhePage />} />
        </Routes>
      </MemoryRouter>,
    )
  }

  it('carrega detalhe e só mostra contato após clique explícito', async () => {
    const user = userEvent.setup()
    renderPage()

    expect(await screen.findByRole('heading', { name: pedido.titulo })).toBeInTheDocument()
    expect(screen.queryByText('11999990000')).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /mostrar contato/i }))

    expect(screen.getByText('11999990000')).toBeInTheDocument()
    expect(screen.getByText(/Posso levar amanhã cedo/i)).toBeInTheDocument()
  })

  it('cria doador e atendimento pelo fluxo Quero ajudar', async () => {
    const user = userEvent.setup()
    renderPage()

    await user.click(await screen.findByRole('button', { name: /quero ajudar/i }))
    await user.type(screen.getByLabelText('Seu nome'), 'Maria')
    await user.type(screen.getByLabelText('Telefone ou WhatsApp'), '11988887777')
    await user.selectOptions(screen.getByLabelText('Tipo de ajuda'), 'ração')
    await user.type(screen.getByLabelText('Observação'), 'Consigo entregar hoje.')
    await user.click(screen.getByRole('button', { name: /confirmar ajuda/i }))

    await waitFor(() =>
      expect(criarDoador).toHaveBeenCalledWith({
        nome: 'Maria',
        telefone: '11988887777',
      }),
    )
    expect(criarAtendimento).toHaveBeenCalledWith(7, {
      doador_id: 11,
      tipo_ajuda: 'ração',
      observacao: 'Consigo entregar hoje.',
    })
    expect(await screen.findByText('Ajuda registrada. Obrigado por apoiar este pedido.')).toBeInTheDocument()
  })
})
