import { renderHook, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { useApi } from './useApi'

describe('useApi', () => {
  it('expõe loading inicial e dados após sucesso', async () => {
    const { result } = renderHook(() => useApi(() => Promise.resolve('ok')))

    expect(result.current.loading).toBe(true)

    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.data).toBe('ok')
    expect(result.current.error).toBeNull()
  })

  it('expõe mensagem de erro quando a chamada falha', async () => {
    const { result } = renderHook(() => useApi(() => Promise.reject(new Error('Falhou'))))

    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.data).toBeNull()
    expect(result.current.error).toBe('Falhou')
  })
})
