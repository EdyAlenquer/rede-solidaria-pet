import type { ReactNode } from 'react'

import { Seo } from '../components/Seo'

type PaginaConteudoProps = {
  /** Eyebrow exibido acima do título. */
  eyebrow: string
  /** Título principal (usado também no SEO). */
  titulo: string
  /** Subtítulo descritivo (usado também como description do SEO). */
  descricao: string
  /** Conteúdo da página (seções de prosa, listas, etc.). */
  children: ReactNode
}

/**
 * Layout base para páginas estáticas de conteúdo (legais e institucionais).
 *
 * Aplica o cabeçalho padrão com eyebrow/título/subtítulo, o SEO da página e
 * envolve o conteúdo em um container de prosa legível.
 *
 * @param props - Eyebrow, título, descrição e conteúdo.
 * @returns Seção estreita com cabeçalho e corpo de conteúdo.
 */
export function PaginaConteudo({ eyebrow, titulo, descricao, children }: PaginaConteudoProps) {
  return (
    <section className="rsp-page rsp-page--narrow rsp-content">
      <Seo title={titulo} description={descricao} />
      <div className="rsp-page__header">
        <div>
          <p className="rsp-eyebrow">{eyebrow}</p>
          <h1 className="rsp-page__title">{titulo}</h1>
          <p className="rsp-page__sub">{descricao}</p>
        </div>
      </div>
      <div className="rsp-content__body">{children}</div>
    </section>
  )
}
