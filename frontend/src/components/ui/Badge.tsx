import type { ReactNode } from 'react'

type BadgeTone = 'neutral' | 'success' | 'warning' | 'danger'

type BadgeProps = {
  children: ReactNode
  tone?: BadgeTone
}

/**
 * Badge textual para status, urgência e categorias.
 *
 * @param props - Conteúdo e tom visual.
 * @returns Marcador visual compacto.
 */
export function Badge({ children, tone = 'neutral' }: BadgeProps) {
  return <span className={`rsp-badge rsp-badge--${tone}`}>{children}</span>
}
