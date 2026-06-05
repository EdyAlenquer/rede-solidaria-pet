import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { RotaProtegida } from './RotaProtegida'
import { AuthProvider } from './AuthContext'
import { me as meRequest } from '../services/api/auth'
import { TOKEN_STORAGE_KEY } from '../services/api/client'

vi.mock('../services/api/auth', () => ({
  login: vi.fn(),
  me: vi.fn(),
  registrar: vi.fn(),
}))

function renderRota(path: string) {
  render(
    <AuthProvider>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route element={<RotaProtegida />}>
            <Route path="/perfil" element={<h1>Área do perfil</h1>} />
          </Route>
          <Route path="/entrar" element={<h1>Entrar</h1>} />
        </Routes>
      </MemoryRouter>
    </AuthProvider>,
  )
}

describe('RotaProtegida', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('redireciona para /entrar quando anônimo', async () => {
    renderRota('/perfil')

    await waitFor(() =>
      expect(screen.getByRole('heading', { name: 'Entrar' })).toBeInTheDocument(),
    )
  })

  it('renderiza a rota protegida quando autenticado', async () => {
    localStorage.setItem(TOKEN_STORAGE_KEY, 'token-valido')
    vi.mocked(meRequest).mockResolvedValue({
      id: 1,
      nome: 'Maria',
      email: 'maria@example.com',
      papel: 'protetor',
    })

    renderRota('/perfil')

    await waitFor(() =>
      expect(screen.getByRole('heading', { name: 'Área do perfil' })).toBeInTheDocument(),
    )
  })
})
