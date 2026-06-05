import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HelmetProvider } from 'react-helmet-async'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { PerfilPage } from './PerfilPage'
import { eliminarMinhaConta, exportarMeusDados } from '../services/api/me'
import type { MeusDados, UsuarioRead } from '../types/api'

vi.mock('../services/api/me', () => ({
  exportarMeusDados: vi.fn(),
  eliminarMinhaConta: vi.fn(),
}))

const logoutMock = vi.fn()
let authState: { usuario: UsuarioRead | null; logout: () => void }
vi.mock('../auth/AuthContext', () => ({
  useAuth: () => authState,
}))

const mostrarMock = vi.fn()
vi.mock('../components/Toast', () => ({
  useToast: () => ({ mostrar: mostrarMock }),
}))

const usuario: UsuarioRead = {
  id: 1,
  nome: 'Ana Autora',
  email: 'ana@x.com',
  papel: 'protetor',
}

const meusDados: MeusDados = {
  perfil: usuario,
  pedidos: [
    {
      id: 7,
      titulo: 'Gata precisa de transporte',
      descricao: 'Precisa ir até a clínica.',
      categoria: 'transporte',
      urgencia: 'alta',
      status: 'aberto',
      data_criacao: '2026-05-27T12:00:00Z',
      cidade: 'São Paulo',
      estado: 'SP',
      contato: '11999990000',
    },
  ],
  atendimentos: [],
}

describe('PerfilPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    authState = { usuario, logout: logoutMock }
    vi.mocked(exportarMeusDados).mockResolvedValue(meusDados)
    vi.mocked(eliminarMinhaConta).mockResolvedValue(undefined)
  })

  function renderPage() {
    render(
      <HelmetProvider>
        <MemoryRouter initialEntries={['/perfil']}>
          <Routes>
            <Route path="/perfil" element={<PerfilPage />} />
            <Route path="/" element={<div>Início</div>} />
          </Routes>
        </MemoryRouter>
      </HelmetProvider>,
    )
  }

  it('mostra dados da conta e a lista de meus pedidos', async () => {
    renderPage()

    expect(await screen.findByText('ana@x.com')).toBeInTheDocument()
    expect(screen.getByText('Ana Autora')).toBeInTheDocument()
    const pedido = await screen.findByRole('link', { name: /gata precisa de transporte/i })
    expect(pedido).toHaveAttribute('href', '/pedidos/7')
  })

  it('exclui a conta após confirmação forte e desloga', async () => {
    const user = userEvent.setup()
    renderPage()
    await screen.findByText('ana@x.com')

    await user.click(screen.getByRole('button', { name: /excluir minha conta/i }))
    const dialog = await screen.findByRole('dialog')
    const confirmar = within(dialog).getByRole('button', { name: /excluir conta/i })
    expect(confirmar).toBeDisabled()

    await user.type(within(dialog).getByLabelText(/digite excluir/i), 'EXCLUIR')
    expect(confirmar).toBeEnabled()
    await user.click(confirmar)

    await waitFor(() => expect(eliminarMinhaConta).toHaveBeenCalledTimes(1))
    expect(logoutMock).toHaveBeenCalledTimes(1)
  })
})
