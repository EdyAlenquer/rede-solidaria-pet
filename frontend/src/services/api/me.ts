import { apiClient } from './client'
import type { MeusDados } from '../../types/api'

/**
 * Exporta os dados pessoais do usuário atual (direito de acesso LGPD).
 *
 * @returns Perfil, pedidos (com contato próprio) e atendimentos do titular.
 */
export async function exportarMeusDados(): Promise<MeusDados> {
  const response = await apiClient.get<MeusDados>('/me/dados')
  return response.data
}

/**
 * Anonimiza e elimina a conta do usuário atual (direito de eliminação LGPD).
 *
 * @returns Nada. Efeito colateral: conta soft-deletada; o token deixa de valer.
 */
export async function eliminarMinhaConta(): Promise<void> {
  await apiClient.delete('/me')
}
