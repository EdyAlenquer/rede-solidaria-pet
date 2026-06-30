import { describe, expect, it, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import { HelmetProvider } from 'react-helmet-async'
import { MemoryRouter } from 'react-router-dom'

import { App } from './App'
import { AuthProvider } from './auth/AuthContext'
import { ToastProvider } from './components/Toast'

vi.mock('./services/api/pedidos', () => ({
  listarPedidos: vi.fn(() => new Promise(() => undefined)),
  obterPedido: vi.fn(() => new Promise(() => undefined)),
}))

vi.mock('./services/api/atendimentos', () => ({
  listarAtendimentos: vi.fn(() => new Promise(() => undefined)),
}))

vi.mock('./services/api/estatisticas', () => ({
  obterEstatisticas: vi.fn(() => new Promise(() => undefined)),
}))

vi.mock('./services/api/auth', () => ({
  login: vi.fn(),
  me: vi.fn(),
  registrar: vi.fn(),
}))

describe('App', () => {
  function renderAt(path: string) {
    render(
      <HelmetProvider>
        <AuthProvider>
          <ToastProvider>
            <MemoryRouter initialEntries={[path]}>
              <App />
            </MemoryRouter>
          </ToastProvider>
        </AuthProvider>
      </HelmetProvider>,
    )
  }

  it('renderiza a rota inicial no layout base', () => {
    renderAt('/')

    expect(screen.getByRole('banner')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /encontre ajuda para um animal/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /ver pedidos/i })).toHaveAttribute('href', '/pedidos')
    expect(screen.getByRole('link', { name: /cadastrar pedido/i })).toHaveAttribute('href', '/pedidos/novo')
    expect(screen.queryByRole('link', { name: /componentes/i })).not.toBeInTheDocument()
  })

  it('exibe a autoria e o contato no rodapé do site', () => {
    renderAt('/')

    const rodape = screen.getByRole('contentinfo')
    expect(rodape).toHaveTextContent(/Francisco Edyvalberty Alenquer Cordeiro/i)

    const repositorio = within(rodape).getByRole('link', {
      name: /github\.com\/edyalenquer\/rede-solidaria-pet/i,
    })
    expect(repositorio).toHaveAttribute(
      'href',
      'https://github.com/EdyAlenquer/rede-solidaria-pet',
    )
  })

  it('renderiza a rota de lista de pedidos', () => {
    renderAt('/pedidos')

    expect(screen.getByRole('heading', { name: /pedidos da comunidade/i })).toBeInTheDocument()
  })

  it('redireciona a rota protegida de novo pedido para o login quando anônimo', async () => {
    renderAt('/pedidos/novo')

    expect(
      await screen.findByRole('heading', { name: /entrar/i, level: 1 }),
    ).toBeInTheDocument()
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
