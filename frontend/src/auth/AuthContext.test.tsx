import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider, useAuth } from './AuthContext'
import { login as loginRequest, me as meRequest } from '../services/api/auth'
import { lerToken, TOKEN_STORAGE_KEY } from '../services/api/client'

vi.mock('../services/api/auth', () => ({
  login: vi.fn(),
  me: vi.fn(),
  registrar: vi.fn(),
}))

function Consumidor() {
  const { usuario, isLoading, login, logout } = useAuth()
  return (
    <div>
      <span data-testid="loading">{isLoading ? 'carregando' : 'pronto'}</span>
      <span data-testid="usuario">{usuario ? usuario.nome : 'anonimo'}</span>
      <button type="button" onClick={() => login({ email: 'a@a.com', senha: 'senha1234' })}>
        entrar
      </button>
      <button type="button" onClick={() => logout()}>
        sair
      </button>
    </div>
  )
}

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('inicia anônimo quando não há token salvo', async () => {
    render(
      <AuthProvider>
        <Consumidor />
      </AuthProvider>,
    )

    await waitFor(() => expect(screen.getByTestId('loading')).toHaveTextContent('pronto'))
    expect(screen.getByTestId('usuario')).toHaveTextContent('anonimo')
    expect(meRequest).not.toHaveBeenCalled()
  })

  it('carrega o usuário atual quando há token salvo', async () => {
    localStorage.setItem(TOKEN_STORAGE_KEY, 'token-valido')
    vi.mocked(meRequest).mockResolvedValue({
      id: 1,
      nome: 'Maria',
      email: 'maria@example.com',
      papel: 'protetor',
    })

    render(
      <AuthProvider>
        <Consumidor />
      </AuthProvider>,
    )

    await waitFor(() => expect(screen.getByTestId('usuario')).toHaveTextContent('Maria'))
  })

  it('salva o token e o usuário ao fazer login', async () => {
    const user = userEvent.setup()
    vi.mocked(loginRequest).mockResolvedValue({ access_token: 'novo-token', token_type: 'bearer' })
    vi.mocked(meRequest).mockResolvedValue({
      id: 2,
      nome: 'João',
      email: 'joao@example.com',
      papel: 'protetor',
    })

    render(
      <AuthProvider>
        <Consumidor />
      </AuthProvider>,
    )
    await waitFor(() => expect(screen.getByTestId('loading')).toHaveTextContent('pronto'))

    await user.click(screen.getByRole('button', { name: 'entrar' }))

    await waitFor(() => expect(screen.getByTestId('usuario')).toHaveTextContent('João'))
    expect(lerToken()).toBe('novo-token')
  })

  it('limpa token e usuário ao sair', async () => {
    const user = userEvent.setup()
    localStorage.setItem(TOKEN_STORAGE_KEY, 'token-valido')
    vi.mocked(meRequest).mockResolvedValue({
      id: 1,
      nome: 'Maria',
      email: 'maria@example.com',
      papel: 'protetor',
    })

    render(
      <AuthProvider>
        <Consumidor />
      </AuthProvider>,
    )
    await waitFor(() => expect(screen.getByTestId('usuario')).toHaveTextContent('Maria'))

    await user.click(screen.getByRole('button', { name: 'sair' }))

    await waitFor(() => expect(screen.getByTestId('usuario')).toHaveTextContent('anonimo'))
    expect(lerToken()).toBeNull()
  })
})
