import { apiClient } from './client'
import type { DenunciaCreate } from '../../types/api'

/**
 * Caminho da coleção de denúncias de um pedido.
 *
 * @param pedidoId - Identificador do pedido.
 * @returns Path REST de denúncias do pedido.
 */
export function denunciasPath(pedidoId: number): string {
  return `/pedidos/${pedidoId}/denuncias`
}

/**
 * Registra uma denúncia para um pedido.
 *
 * @param pedidoId - Identificador do pedido.
 * @param payload - Motivo e descrição opcional da denúncia.
 * @returns Nada. Efeito colateral: denúncia criada no backend.
 */
export async function denunciarPedido(pedidoId: number, payload: DenunciaCreate): Promise<void> {
  await apiClient.post(denunciasPath(pedidoId), payload)
}
