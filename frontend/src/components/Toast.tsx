import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'

export type ToastTom = 'info' | 'sucesso' | 'erro'

type Toast = {
  id: number
  mensagem: string
  tom: ToastTom
}

type ToastContextValue = {
  /** Exibe um toast e o anuncia em região aria-live. */
  mostrar: (mensagem: string, tom?: ToastTom) => void
}

const ToastContext = createContext<ToastContextValue | null>(null)

const DURACAO_MS = 5000

type ToastProviderProps = {
  children: ReactNode
}

/**
 * Provedor de notificações efêmeras com região assistiva `aria-live`.
 *
 * A região `role="status" aria-live="polite"` permanece sempre no DOM para que
 * leitores de tela anunciem mensagens adicionadas dinamicamente.
 *
 * @param props - Filhos que poderão disparar toasts.
 * @returns Provedor React do contexto de toasts.
 */
export function ToastProvider({ children }: ToastProviderProps) {
  const [toasts, setToasts] = useState<Toast[]>([])
  const proximoId = useRef(1)

  const remover = useCallback((id: number) => {
    setToasts((atuais) => atuais.filter((toast) => toast.id !== id))
  }, [])

  const mostrar = useCallback(
    (mensagem: string, tom: ToastTom = 'info') => {
      const id = proximoId.current
      proximoId.current += 1
      setToasts((atuais) => [...atuais, { id, mensagem, tom }])
      window.setTimeout(() => remover(id), DURACAO_MS)
    },
    [remover],
  )

  const value = useMemo<ToastContextValue>(() => ({ mostrar }), [mostrar])

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="rsp-toast-region" role="status" aria-live="polite">
        {toasts.map((toast) => (
          <div key={toast.id} className={`rsp-toast rsp-toast--${toast.tom}`}>
            <span>{toast.mensagem}</span>
            <button
              type="button"
              className="rsp-toast__close"
              aria-label="Fechar aviso"
              onClick={() => remover(toast.id)}
            >
              ×
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

/**
 * Acessa o contexto de toasts.
 *
 * @returns Função `mostrar` para anunciar mensagens.
 * @throws Error quando usado fora de um `ToastProvider`.
 */
export function useToast(): ToastContextValue {
  const context = useContext(ToastContext)
  if (context === null) {
    throw new Error('useToast deve ser usado dentro de um ToastProvider.')
  }
  return context
}
