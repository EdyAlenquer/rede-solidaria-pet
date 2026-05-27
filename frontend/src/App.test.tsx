import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

import { App } from './App'

vi.mock('./services/api/pedidos', () => ({
  listarPedidos: vi.fn(() => new Promise(() => undefined)),
  obterPedido: vi.fn(() => new Promise(() => undefined)),
}))

vi.mock('./services/api/atendimentos', () => ({
  listarAtendimentos: vi.fn(() => new Promise(() => undefined)),
}))

describe('App', () => {
  function renderAt(path: string) {
    render(
      <MemoryRouter initialEntries={[path]}>
        <App />
      </MemoryRouter>,
    )
  }

  it('renderiza a rota inicial no layout base', () => {
    renderAt('/')

    expect(screen.getByRole('banner')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /bem-vindo/i })).toBeInTheDocument()
  })

  it('renderiza a rota de lista de pedidos', () => {
    renderAt('/pedidos')

    expect(screen.getByRole('heading', { name: /pedidos da comunidade/i })).toBeInTheDocument()
  })

  it('renderiza a rota de novo pedido', () => {
    renderAt('/pedidos/novo')

    expect(screen.getByRole('heading', { name: /novo pedido/i })).toBeInTheDocument()
  })

  it('renderiza a rota de detalhe do pedido', () => {
    renderAt('/pedidos/123')

    expect(screen.getByText(/carregando pedido/i)).toBeInTheDocument()
  })

  it('renderiza o playground de componentes base', () => {
    renderAt('/__playground__')

    expect(screen.getByRole('heading', { name: /playground/i })).toBeInTheDocument()
  })
})
