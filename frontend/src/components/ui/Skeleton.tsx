type SkeletonProps = {
  /** Quantidade de cartões-fantasma a exibir. */
  itens?: number
  /** Rótulo acessível anunciado enquanto carrega. */
  rotulo?: string
}

/**
 * Placeholder de carregamento com efeito shimmer e contagem configurável.
 *
 * Respeita `prefers-reduced-motion` (a animação é desligada via CSS). Expõe um
 * `role="status"` com rótulo assistivo para anunciar o carregamento; os blocos
 * visuais são decorativos (`aria-hidden`).
 *
 * @param props - Número de itens e rótulo acessível.
 * @returns Grade de cartões-fantasma.
 */
export function Skeleton({ itens = 6, rotulo = 'Carregando…' }: SkeletonProps) {
  return (
    <div className="rsp-feed__grid" role="status" aria-live="polite">
      <span className="rsp-sr-only">{rotulo}</span>
      {Array.from({ length: itens }, (_, indice) => (
        <div key={indice} className="rsp-skel-card" aria-hidden="true">
          <div className="rsp-skel rsp-skel--thumb" />
          <div className="rsp-skel rsp-skel--line" />
          <div className="rsp-skel rsp-skel--line rsp-skel--short" />
          <div className="rsp-skel rsp-skel--chip" />
        </div>
      ))}
    </div>
  )
}
