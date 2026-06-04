import { apiClient } from './client'
import type {
  LoginPayload,
  RegistroPayload,
  TokenResponse,
  UsuarioRead,
} from '../../types/api'

/**
 * Registra um novo usuário (protetor).
 *
 * @param payload - Dados de cadastro com aceite do consentimento LGPD.
 * @returns Usuário criado (sem senha).
 */
export async function registrar(payload: RegistroPayload): Promise<UsuarioRead> {
  const response = await apiClient.post<UsuarioRead>('/auth/registro', payload)
  return response.data
}

/**
 * Autentica e obtém um access token.
 *
 * @param payload - E-mail e senha.
 * @returns Token de acesso (`bearer`).
 */
export async function login(payload: LoginPayload): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>('/auth/login', payload)
  return response.data
}

/**
 * Recupera o usuário autenticado a partir do token vigente.
 *
 * @returns Dados do usuário atual.
 */
export async function me(): Promise<UsuarioRead> {
  const response = await apiClient.get<UsuarioRead>('/auth/me')
  return response.data
}
