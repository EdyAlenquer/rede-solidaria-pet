import { apiClient } from './client'
import type { Pedido, PedidoCreate, PedidoPage, StatusPedido } from '../../types/api'

export type PedidoListParams = {
  categoria?: string
  page?: number
  page_size?: number
  q?: string
  status?: StatusPedido
  urgencia?: string
}

/**
 * Caminho da coleção de pedidos.
 *
 * @returns Path REST de pedidos.
 */
export function pedidosPath() {
  return '/pedidos'
}

/**
 * Caminho de um pedido específico.
 *
 * @param pedidoId - Identificador do pedido.
 * @returns Path REST do pedido.
 */
export function pedidoPath(pedidoId: number) {
  return `${pedidosPath()}/${pedidoId}`
}

/**
 * Lista pedidos com filtros opcionais.
 *
 * @param params - Filtros e paginação.
 * @returns Página de pedidos retornada pela API.
 */
export async function listarPedidos(params: PedidoListParams = {}) {
  const response = await apiClient.get<PedidoPage>(pedidosPath(), { params })
  return response.data
}

/**
 * Cria um pedido de ajuda.
 *
 * @param payload - Dados do novo pedido.
 * @returns Pedido criado pela API.
 */
export async function criarPedido(payload: PedidoCreate) {
  const response = await apiClient.post<Pedido>(pedidosPath(), payload)
  return response.data
}

/**
 * Busca um pedido por id.
 *
 * @param pedidoId - Identificador do pedido.
 * @returns Pedido encontrado.
 */
export async function obterPedido(pedidoId: number) {
  const response = await apiClient.get<Pedido>(pedidoPath(pedidoId))
  return response.data
}
