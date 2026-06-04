import axios from 'axios'

const DEFAULT_API_BASE_URL = '/api/v1'

/** Chave do token JWT no `localStorage`. */
export const TOKEN_STORAGE_KEY = 'rsp.token'

/**
 * Lê o token JWT persistido.
 *
 * @returns Token salvo, ou `null` quando não há sessão.
 */
export function lerToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_STORAGE_KEY)
  } catch {
    return null
  }
}

/**
 * Persiste ou remove o token JWT.
 *
 * @param token - Token a salvar, ou `null` para limpar a sessão.
 * @returns Nada. Efeito colateral: grava/remove em `localStorage`.
 */
export function salvarToken(token: string | null): void {
  try {
    if (token) {
      localStorage.setItem(TOKEN_STORAGE_KEY, token)
    } else {
      localStorage.removeItem(TOKEN_STORAGE_KEY)
    }
  } catch {
    // Ambiente sem localStorage (ex.: SSR/teste): ignora silenciosamente.
  }
}

/**
 * Cliente HTTP compartilhado da API.
 *
 * @returns Instância Axios com `baseURL` configurada por ambiente.
 */
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL,
  headers: {
    Accept: 'application/json',
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.request.use((config) => {
  const token = lerToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      salvarToken(null)
    }
    return Promise.reject(error)
  },
)
