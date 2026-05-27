import type { ReactNode } from 'react'

type CardProps = {
  children: ReactNode
  title: string
}

/**
 * Card base para conteúdo destacado.
 *
 * @param props - Título acessível e conteúdo do card.
 * @returns Região nomeada com estilo de card.
 */
export function Card({ children, title }: CardProps) {
  return (
    <section className="rsp-card" aria-label={title}>
      <h2 className="rsp-card__title">{title}</h2>
      <div className="rsp-card__body">{children}</div>
    </section>
  )
}
