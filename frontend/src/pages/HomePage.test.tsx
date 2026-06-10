import { render, screen } from '@testing-library/react'
import { HelmetProvider } from 'react-helmet-async'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { HomePage } from './HomePage'
import { obterEstatisticas } from '../services/api/estatisticas'
import type { Estatisticas } from '../types/api'

vi.mock('../services/api/estatisticas', () => ({
  obterEstatisticas: vi.fn(),
}))

const estatisticas: Estatisticas = {
  total_pedidos: 128,
  pedidos_abertos: 42,
  pedidos_concluidos: 73,
  total_atendimentos: 215,
  total_cidades: 19,
}

describe('HomePage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  function renderPage() {
    render(
      <HelmetProvider>
        <MemoryRouter>
          <HomePage />
        </MemoryRouter>
      </HelmetProvider>,
    )
  }

  it('mostra o título, CTAs e a seção "como funciona"', () => {
    vi.mocked(obterEstatisticas).mockImplementation(() => new Promise(() => undefined))
    renderPage()

    expect(
      screen.getByRole('heading', { name: /encontre ajuda para um animal/i, level: 1 }),
    ).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /ver pedidos/i })).toHaveAttribute('href', '/pedidos')
    expect(screen.getByRole('link', { name: /cadastrar pedido/i })).toHaveAttribute(
      'href',
      '/pedidos/novo',
    )
    expect(
      screen.getByRole('img', { name: /filhotes aguardando ajuda comunitária/i }),
    ).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /como funciona/i })).toBeInTheDocument()
  })

  it('exibe os contadores reais vindos da API de estatísticas', async () => {
    vi.mocked(obterEstatisticas).mockResolvedValue(estatisticas)
    renderPage()

    expect(obterEstatisticas).toHaveBeenCalledTimes(1)
    // Pedidos publicados (total).
    expect(await screen.findByText('128')).toBeInTheDocument()
    // Atendimentos registrados.
    expect(screen.getByText('215')).toBeInTheDocument()
    // Cidades alcançadas.
    expect(screen.getByText('19')).toBeInTheDocument()
    // Pedidos concluídos (animais ajudados).
    expect(screen.getByText('73')).toBeInTheDocument()
  })

  it('não quebra quando a API de estatísticas falha', async () => {
    vi.mocked(obterEstatisticas).mockRejectedValue(new Error('falhou'))
    renderPage()

    expect(
      await screen.findByRole('heading', { name: /encontre ajuda para um animal/i }),
    ).toBeInTheDocument()
    // Sem números, mas a página segue utilizável (placeholder neutro).
    expect(screen.getAllByText('—').length).toBeGreaterThan(0)
  })
})
