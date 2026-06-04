/**
 * Helpers de apresentação de pedidos (puros, sem efeitos colaterais).
 *
 * Resolvem a primeira imagem, o tom de badge da urgência e a montagem de
 * coordenadas, mantendo as páginas livres de lógica repetida.
 */

import type { Pedido, Urgencia } from '../types/api'

type BadgeTone = 'neutral' | 'success' | 'warning' | 'danger'

/**
 * Tom visual do badge de urgência.
 *
 * @param urgencia - Nível de urgência do pedido.
 * @returns Tom do `Badge` correspondente.
 */
export function tomUrgencia(urgencia: Urgencia): BadgeTone {
  if (urgencia === 'alta') {
    return 'danger'
  }
  if (urgencia === 'media') {
    return 'warning'
  }
  return 'success'
}

/**
 * URL da primeira imagem do pedido (capa), se houver.
 *
 * As imagens são servidas em caminhos relativos (`/uploads/...`) e o `ordem`
 * define a sequência; usamos a de menor `ordem` como capa.
 *
 * @param pedido - Pedido a inspecionar.
 * @returns URL da imagem de capa, ou `null` quando não há fotos.
 */
export function urlCapa(pedido: Pedido): string | null {
  const imagens = pedido.imagens ?? []
  if (imagens.length === 0) {
    return null
  }
  const ordenadas = [...imagens].sort((a, b) => a.ordem - b.ordem)
  return ordenadas[0].url
}

/**
 * Indica se o pedido tem coordenadas válidas para exibir no mapa.
 *
 * @param pedido - Pedido a inspecionar.
 * @returns `true` quando latitude e longitude são números finitos.
 */
export function temCoordenadas<T extends Pick<Pedido, 'latitude' | 'longitude'>>(
  pedido: T,
): pedido is T & { latitude: number; longitude: number } {
  return (
    typeof pedido.latitude === 'number' &&
    Number.isFinite(pedido.latitude) &&
    typeof pedido.longitude === 'number' &&
    Number.isFinite(pedido.longitude)
  )
}

/**
 * Texto curto de localização "Cidade, UF" (ou apenas o que existir).
 *
 * @param pedido - Pedido a inspecionar.
 * @returns Localização formatada, ou string vazia quando não informada.
 */
export function rotuloLocalizacao(pedido: Pick<Pedido, 'cidade' | 'estado'>): string {
  return [pedido.cidade, pedido.estado].filter(Boolean).join(', ')
}
