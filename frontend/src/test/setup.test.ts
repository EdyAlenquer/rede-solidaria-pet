import { describe, expect, it } from 'vitest'

describe('ambiente de testes', () => {
  it('disponibiliza localStorage para testes de autenticação', () => {
    localStorage.setItem('rede-solidaria-pet:test', 'ok')

    expect(localStorage.getItem('rede-solidaria-pet:test')).toBe('ok')
  })
})
