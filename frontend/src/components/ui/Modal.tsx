import { useCallback, useEffect, useId, useRef, type KeyboardEvent, type ReactNode } from 'react'

type ModalProps = {
  /** Controla a visibilidade do diálogo. */
  open: boolean
  /** Chamado ao pedir fechamento (ESC, overlay ou botão de fechar). */
  onClose: () => void
  /** Título acessível exibido no topo e associado via `aria-labelledby`. */
  titulo: string
  /** Conteúdo do corpo do diálogo. */
  children: ReactNode
  /** Rodapé opcional (botões de ação). */
  rodape?: ReactNode
}

const SELETOR_FOCAVEIS =
  'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'

/**
 * Diálogo modal acessível e reutilizável.
 *
 * Implementa `role="dialog"` com `aria-modal`, título associado por
 * `aria-labelledby`, fechamento por ESC / clique no overlay / botão de fechar,
 * foco inicial movido para dentro do diálogo e armadilha de foco (Tab/Shift+Tab
 * circulam apenas pelos elementos internos). Ao fechar, devolve o foco ao
 * elemento que estava ativo antes da abertura.
 *
 * @param props - Estado de abertura, callback de fechamento, título, corpo e rodapé.
 * @returns O diálogo quando aberto, ou `null` quando fechado.
 */
export function Modal({ open, onClose, titulo, children, rodape }: ModalProps) {
  const tituloId = useId()
  const dialogRef = useRef<HTMLDivElement>(null)
  const fecharRef = useRef<HTMLButtonElement>(null)
  const gatilhoRef = useRef<HTMLElement | null>(null)

  useEffect(() => {
    if (!open) {
      return
    }
    gatilhoRef.current = document.activeElement as HTMLElement | null
    // Foca o primeiro elemento interno focável (ou o botão de fechar).
    const focaveis = dialogRef.current?.querySelectorAll<HTMLElement>(SELETOR_FOCAVEIS)
    const primeiro = focaveis && focaveis.length > 0 ? focaveis[0] : fecharRef.current
    primeiro?.focus()
    return () => {
      gatilhoRef.current?.focus?.()
    }
  }, [open])

  const handleKeyDown = useCallback(
    (event: KeyboardEvent<HTMLDivElement>) => {
      if (event.key === 'Escape') {
        event.stopPropagation()
        onClose()
        return
      }
      if (event.key !== 'Tab') {
        return
      }
      const focaveis = dialogRef.current?.querySelectorAll<HTMLElement>(SELETOR_FOCAVEIS)
      if (!focaveis || focaveis.length === 0) {
        return
      }
      const primeiro = focaveis[0]
      const ultimo = focaveis[focaveis.length - 1]
      const ativo = document.activeElement
      if (event.shiftKey && ativo === primeiro) {
        event.preventDefault()
        ultimo.focus()
      } else if (!event.shiftKey && ativo === ultimo) {
        event.preventDefault()
        primeiro.focus()
      }
    },
    [onClose],
  )

  if (!open) {
    return null
  }

  return (
    <div className="rsp-modal-overlay" onMouseDown={onClose}>
      <div
        ref={dialogRef}
        className="rsp-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby={tituloId}
        onKeyDown={handleKeyDown}
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="rsp-modal__head">
          <h2 id={tituloId} className="rsp-modal__title">
            {titulo}
          </h2>
          <button
            ref={fecharRef}
            type="button"
            className="rsp-modal__close"
            aria-label="Fechar"
            onClick={onClose}
          >
            ×
          </button>
        </div>
        <div className="rsp-modal__body">{children}</div>
        {rodape && <div className="rsp-modal__footer">{rodape}</div>}
      </div>
    </div>
  )
}
