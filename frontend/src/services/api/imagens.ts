import { apiClient } from './client'
import type { ImagemRead } from '../../types/api'

/**
 * Caminho da coleção de imagens de um pedido.
 *
 * @param pedidoId - Identificador do pedido.
 * @returns Path REST das imagens do pedido.
 */
export function imagensPath(pedidoId: number): string {
  return `/pedidos/${pedidoId}/imagens`
}

/**
 * Envia uma imagem (multipart) para um pedido.
 *
 * @param pedidoId - Identificador do pedido.
 * @param arquivo - Arquivo de imagem (jpeg, png ou webp).
 * @returns Metadados da imagem criada.
 */
export async function enviarImagem(pedidoId: number, arquivo: File): Promise<ImagemRead> {
  const formData = new FormData()
  formData.append('arquivo', arquivo)
  const response = await apiClient.post<ImagemRead>(imagensPath(pedidoId), formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

/**
 * Lista as imagens de um pedido.
 *
 * @param pedidoId - Identificador do pedido.
 * @returns Lista de imagens ordenadas pela `ordem`.
 */
export async function listarImagens(pedidoId: number): Promise<ImagemRead[]> {
  const response = await apiClient.get<ImagemRead[]>(imagensPath(pedidoId))
  return response.data
}

/**
 * Remove uma imagem de um pedido.
 *
 * @param pedidoId - Identificador do pedido.
 * @param imagemId - Identificador da imagem.
 * @returns Nada. Efeito colateral: imagem removida no backend.
 */
export async function removerImagem(pedidoId: number, imagemId: number): Promise<void> {
  await apiClient.delete(`${imagensPath(pedidoId)}/${imagemId}`)
}
