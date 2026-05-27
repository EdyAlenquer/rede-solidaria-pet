import { apiClient } from './client'
import type { Doador, DoadorCreate } from '../../types/api'

/**
 * Caminho da coleção de doadores.
 *
 * @returns Path REST de doadores.
 */
export function doadoresPath() {
  return '/doadores'
}

/**
 * Caminho de um doador específico.
 *
 * @param doadorId - Identificador do doador.
 * @returns Path REST do doador.
 */
export function doadorPath(doadorId: number) {
  return `${doadoresPath()}/${doadorId}`
}

/**
 * Cria um doador ou voluntário.
 *
 * @param payload - Dados do doador.
 * @returns Doador criado pela API.
 */
export async function criarDoador(payload: DoadorCreate) {
  const response = await apiClient.post<Doador>(doadoresPath(), payload)
  return response.data
}

/**
 * Busca um doador por id para uso administrativo.
 *
 * @param doadorId - Identificador do doador.
 * @returns Doador encontrado.
 */
export async function obterDoador(doadorId: number) {
  const response = await apiClient.get<Doador>(doadorPath(doadorId))
  return response.data
}
