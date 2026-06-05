import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HelmetProvider } from 'react-helmet-async'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { CadastroPage } from './CadastroPage'

const registrarMock = vi.fn()
const mostrarMock = vi.fn()
const navigateMock = vi.fn()

vi.mock('../auth/AuthContext', () => ({
  useAuth: () => ({ registrar: registrarMock, isAuthenticated: false }),
}))

vi.mock('../components/Toast', () => ({
  useToast: () => ({ mostrar: mostrarMock }),
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return {
    ...actual,
    useNavigate: () => navigateMock,
    useLocation: () => ({ pathname: '/cadastrar', state: null }),
  }
})

function renderPage() {
  render(
    <HelmetProvider>
      <MemoryRouter initialEntries={['/cadastrar']}>
        <CadastroPage />
      </MemoryRouter>
    </HelmetProvider>,
  )
}

describe('CadastroPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    registrarMock.mockResolvedValue(undefined)
  })

  it('valida campos e o consentimento obrigatório', async () => {
    const user = userEvent.setup()
    renderPage()

    await user.click(screen.getByRole('button', { name: /criar conta/i }))

    expect(screen.getByText('Informe seu nome.')).toBeInTheDocument()
    expect(screen.getByText('Informe um e-mail válido.')).toBeInTheDocument()
    expect(screen.getByText('A senha deve ter pelo menos 8 caracteres.')).toBeInTheDocument()
    expect(screen.getByText('É necessário aceitar a política de privacidade.')).toBeInTheDocument()
    expect(registrarMock).not.toHaveBeenCalled()
  })

  it('registra com consentimento e redireciona', async () => {
    const user = userEvent.setup()
    renderPage()

    await user.type(screen.getByLabelText('Nome'), 'Maria Silva')
    await user.type(screen.getByLabelText('E-mail'), 'maria@example.com')
    await user.type(screen.getByLabelText('Senha'), 'senha1234')
    await user.click(screen.getByLabelText(/aceito a política de privacidade/i))
    await user.click(screen.getByRole('button', { name: /criar conta/i }))

    await waitFor(() =>
      expect(registrarMock).toHaveBeenCalledWith({
        nome: 'Maria Silva',
        email: 'maria@example.com',
        senha: 'senha1234',
        consentimento_aceito: true,
      }),
    )
    expect(navigateMock).toHaveBeenCalledWith('/pedidos', { replace: true })
    expect(mostrarMock).toHaveBeenCalled()
  })

  it('inclui o telefone quando informado', async () => {
    const user = userEvent.setup()
    renderPage()

    await user.type(screen.getByLabelText('Nome'), 'Maria Silva')
    await user.type(screen.getByLabelText('E-mail'), 'maria@example.com')
    await user.type(screen.getByLabelText('Senha'), 'senha1234')
    await user.type(screen.getByLabelText(/telefone/i), '11999990000')
    await user.click(screen.getByLabelText(/aceito a política de privacidade/i))
    await user.click(screen.getByRole('button', { name: /criar conta/i }))

    await waitFor(() =>
      expect(registrarMock).toHaveBeenCalledWith(
        expect.objectContaining({ telefone: '(11) 99999-0000' }),
      ),
    )
  })

  it('mostra erro quando o e-mail já está em uso', async () => {
    const user = userEvent.setup()
    registrarMock.mockRejectedValue({ response: { status: 409 } })
    renderPage()

    await user.type(screen.getByLabelText('Nome'), 'Maria Silva')
    await user.type(screen.getByLabelText('E-mail'), 'maria@example.com')
    await user.type(screen.getByLabelText('Senha'), 'senha1234')
    await user.click(screen.getByLabelText(/aceito a política de privacidade/i))
    await user.click(screen.getByRole('button', { name: /criar conta/i }))

    expect(
      await screen.findByText('Este e-mail já está cadastrado. Tente entrar.'),
    ).toBeInTheDocument()
    expect(navigateMock).not.toHaveBeenCalled()
  })
})
