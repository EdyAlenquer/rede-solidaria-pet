import { apiClient } from './client'
import type { Estatisticas } from '../../types/api'

/**
 * Caminho do recurso de estatísticas públicas.
 *
 * @returns Path REST de estatísticas.
 */
export function estatisticasPath(): string {
  return '/estatisticas'
}

/**
 * Busca os contadores agregados públicos.
 *
 * @returns Estatísticas do painel público.
 */
export async function obterEstatisticas(): Promise<Estatisticas> {
  const response = await apiClient.get<Estatisticas>(estatisticasPath())
  return response.data
}
