import { afterEach, describe, expect, it, vi } from 'vitest'

describe('apiClient', () => {
  afterEach(() => {
    vi.resetModules()
    vi.unstubAllEnvs()
  })

  it('usa /api/v1 como baseURL padrão', async () => {
    const { apiClient } = await import('./client')

    expect(apiClient.defaults.baseURL).toBe('/api/v1')
  })

  it('respeita VITE_API_BASE_URL quando informado', async () => {
    vi.stubEnv('VITE_API_BASE_URL', 'http://localhost:8000/api/v1')

    const { apiClient } = await import('./client')

    expect(apiClient.defaults.baseURL).toBe('http://localhost:8000/api/v1')
  })

  it('monta caminhos dos endpoints de pedidos, doadores e atendimentos', async () => {
    const pedidos = await import('./pedidos')
    const doadores = await import('./doadores')
    const atendimentos = await import('./atendimentos')

    expect(pedidos.pedidosPath()).toBe('/pedidos')
    expect(pedidos.pedidoPath(7)).toBe('/pedidos/7')
    expect(doadores.doadorPath(2)).toBe('/doadores/2')
    expect(atendimentos.atendimentosPath(7)).toBe('/pedidos/7/atendimentos')
  })
})
