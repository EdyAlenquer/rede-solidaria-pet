import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HelmetProvider } from 'react-helmet-async'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { LoginPage } from './LoginPage'

const loginMock = vi.fn()
const mostrarMock = vi.fn()
const navigateMock = vi.fn()

vi.mock('../auth/AuthContext', () => ({
  useAuth: () => ({ login: loginMock, isAuthenticated: false }),
}))

vi.mock('../components/Toast', () => ({
  useToast: () => ({ mostrar: mostrarMock }),
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return {
    ...actual,
    useNavigate: () => navigateMock,
    useLocation: () => ({ pathname: '/entrar', state: null }),
  }
})

function renderPage() {
  render(
    <HelmetProvider>
      <MemoryRouter initialEntries={['/entrar']}>
        <LoginPage />
      </MemoryRouter>
    </HelmetProvider>,
  )
}

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    loginMock.mockResolvedValue(undefined)
  })

  it('valida campos obrigatórios e não chama a API', async () => {
    const user = userEvent.setup()
    renderPage()

    await user.click(screen.getByRole('button', { name: /entrar/i }))

    expect(screen.getByText('Informe um e-mail válido.')).toBeInTheDocument()
    expect(screen.getByText('Informe sua senha.')).toBeInTheDocument()
    expect(loginMock).not.toHaveBeenCalled()
  })

  it('autentica e redireciona para /pedidos no sucesso', async () => {
    const user = userEvent.setup()
    renderPage()

    await user.type(screen.getByLabelText('E-mail'), 'maria@example.com')
    await user.type(screen.getByLabelText('Senha'), 'senha1234')
    await user.click(screen.getByRole('button', { name: /entrar/i }))

    await waitFor(() =>
      expect(loginMock).toHaveBeenCalledWith({
        email: 'maria@example.com',
        senha: 'senha1234',
      }),
    )
    expect(navigateMock).toHaveBeenCalledWith('/pedidos', { replace: true })
    expect(mostrarMock).toHaveBeenCalled()
  })

  it('mostra erro de credenciais quando o login falha', async () => {
    const user = userEvent.setup()
    loginMock.mockRejectedValue(new Error('401'))
    renderPage()

    await user.type(screen.getByLabelText('E-mail'), 'maria@example.com')
    await user.type(screen.getByLabelText('Senha'), 'senhaerrada')
    await user.click(screen.getByRole('button', { name: /entrar/i }))

    expect(await screen.findByText('E-mail ou senha inválidos.')).toBeInTheDocument()
    expect(navigateMock).not.toHaveBeenCalled()
  })
})
