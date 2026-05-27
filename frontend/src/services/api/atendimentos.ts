import { apiClient } from './client'
import type { Atendimento, AtendimentoCreate } from '../../types/api'

/**
 * Caminho da coleção de atendimentos de um pedido.
 *
 * @param pedidoId - Identificador do pedido.
 * @returns Path REST de atendimentos do pedido.
 */
export function atendimentosPath(pedidoId: number) {
  return `/pedidos/${pedidoId}/atendimentos`
}

/**
 * Lista atendimentos públicos de um pedido.
 *
 * @param pedidoId - Identificador do pedido.
 * @returns Lista de atendimentos sem dados privados do doador.
 */
export async function listarAtendimentos(pedidoId: number) {
  const response = await apiClient.get<Atendimento[]>(atendimentosPath(pedidoId))
  return response.data
}

/**
 * Registra atendimento para um pedido.
 *
 * @param pedidoId - Identificador do pedido.
 * @param payload - Dados do atendimento.
 * @returns Atendimento criado.
 */
export async function criarAtendimento(pedidoId: number, payload: AtendimentoCreate) {
  const response = await apiClient.post<Atendimento>(atendimentosPath(pedidoId), payload)
  return response.data
}
