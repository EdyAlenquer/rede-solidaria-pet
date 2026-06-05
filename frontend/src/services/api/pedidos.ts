import { apiClient } from './client'
import type {
  Pedido,
  PedidoContato,
  PedidoCreate,
  PedidoPage,
  PedidoUpdate,
  StatusPedido,
} from '../../types/api'

export type PedidoListParams = {
  categoria?: string
  cidade?: string
  estado?: string
  especie?: string
  latitude?: number
  longitude?: number
  page?: number
  page_size?: number
  porte?: string
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

/**
 * Edita parcialmente um pedido (apenas autor ou admin).
 *
 * @param pedidoId - Identificador do pedido.
 * @param payload - Campos a atualizar.
 * @returns Pedido atualizado.
 */
export async function editarPedido(pedidoId: number, payload: PedidoUpdate) {
  const response = await apiClient.patch<Pedido>(pedidoPath(pedidoId), payload)
  return response.data
}

/**
 * Exclui (soft-delete) um pedido (apenas autor ou admin).
 *
 * @param pedidoId - Identificador do pedido.
 * @returns Nada. Efeito colateral: pedido marcado como removido.
 */
export async function excluirPedido(pedidoId: number): Promise<void> {
  await apiClient.delete(pedidoPath(pedidoId))
}

/**
 * Altera o status de um pedido (apenas autor ou admin).
 *
 * @param pedidoId - Identificador do pedido.
 * @param status - Novo status.
 * @returns Pedido atualizado.
 */
export async function alterarStatusPedido(pedidoId: number, status: StatusPedido) {
  const response = await apiClient.patch<Pedido>(`${pedidoPath(pedidoId)}/status`, { status })
  return response.data
}

/**
 * Revela o contato protegido de um pedido (requer autenticação).
 *
 * @param pedidoId - Identificador do pedido.
 * @returns Contato e, quando aplicável, o link de WhatsApp.
 */
export async function revelarContato(pedidoId: number): Promise<PedidoContato> {
  const response = await apiClient.get<PedidoContato>(`${pedidoPath(pedidoId)}/contato`)
  return response.data
}
