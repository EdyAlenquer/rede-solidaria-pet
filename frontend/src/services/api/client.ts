import axios from 'axios'

const DEFAULT_API_BASE_URL = '/api/v1'

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
