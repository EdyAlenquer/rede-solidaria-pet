import { useEffect, useRef, useState } from 'react'

type UseApiState<T> = {
  data: T | null
  error: string | null
  loading: boolean
}

/**
 * Executa uma chamada assíncrona e normaliza loading, erro e dados.
 *
 * @param request - Função assíncrona que busca os dados.
 * @returns Estado atual da chamada.
 */
export function useApi<T>(request: () => Promise<T>): UseApiState<T> {
  const requestRef = useRef(request)
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    error: null,
    loading: true,
  })

  useEffect(() => {
    let active = true

    setState({ data: null, error: null, loading: true })
    requestRef.current()
      .then((data) => {
        if (active) {
          setState({ data, error: null, loading: false })
        }
      })
      .catch((error: unknown) => {
        if (!active) {
          return
        }
        const message = error instanceof Error ? error.message : 'Não foi possível carregar os dados.'
        setState({ data: null, error: message, loading: false })
      })

    return () => {
      active = false
    }
  }, [])

  return state
}
