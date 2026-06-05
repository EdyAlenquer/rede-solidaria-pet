import { render, screen } from '@testing-library/react'
import { HelmetProvider } from 'react-helmet-async'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { ContatoPage } from './ContatoPage'
import { FaqPage } from './FaqPage'
import { PrivacidadePage } from './PrivacidadePage'
import { SobrePage } from './SobrePage'
import { TermosPage } from './TermosPage'

/**
 * Renderiza uma página estática dentro dos provedores mínimos (Helmet + Router).
 *
 * @param ui - Elemento da página a renderizar.
 * @returns Nada; usa o screen global do Testing Library.
 */
function renderPagina(ui: React.ReactElement) {
  render(
    <HelmetProvider>
      <MemoryRouter>{ui}</MemoryRouter>
    </HelmetProvider>,
  )
}

describe('Páginas legais e institucionais', () => {
  it('renderiza a Política de Privacidade com seções de LGPD', () => {
    renderPagina(<PrivacidadePage />)

    expect(
      screen.getByRole('heading', { name: /política de privacidade/i, level: 1 }),
    ).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /dados que coletamos/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /seus direitos/i })).toBeInTheDocument()
    expect(screen.getByText(/lei geral de proteção de dados/i)).toBeInTheDocument()
    // O titular pode acessar e excluir os dados pelo Perfil.
    const linksPerfil = screen.getAllByRole('link', { name: /perfil/i })
    expect(linksPerfil.length).toBeGreaterThan(0)
    expect(linksPerfil[0]).toHaveAttribute('href', '/perfil')
  })

  it('renderiza os Termos de Uso', () => {
    renderPagina(<TermosPage />)

    expect(
      screen.getByRole('heading', { name: /termos de uso/i, level: 1 }),
    ).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /uso da plataforma/i })).toBeInTheDocument()
  })

  it('renderiza a página Sobre com os ODS', () => {
    renderPagina(<SobrePage />)

    expect(screen.getByRole('heading', { name: /^sobre/i, level: 1 })).toBeInTheDocument()
    expect(
      screen.getByRole('heading', { name: /objetivos de desenvolvimento sustentável/i }),
    ).toBeInTheDocument()
  })

  it('renderiza a página de Contato com canais', () => {
    renderPagina(<ContatoPage />)

    expect(screen.getByRole('heading', { name: /contato/i, level: 1 })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /contato@redesolidariapet/i })).toHaveAttribute(
      'href',
      expect.stringContaining('mailto:'),
    )
  })

  it('renderiza o FAQ com perguntas frequentes', () => {
    renderPagina(<FaqPage />)

    expect(
      screen.getByRole('heading', { name: /perguntas frequentes/i, level: 1 }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('group', { name: /como publico um pedido/i }),
    ).toBeInTheDocument()
  })
})
