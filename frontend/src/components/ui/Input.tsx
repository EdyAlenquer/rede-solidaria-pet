import { forwardRef, type InputHTMLAttributes } from 'react'

type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  id: string
  label: string
  /** Mensagem de erro a exibir abaixo do campo (ativa o estado inválido). */
  error?: string | null
}

/**
 * Campo de texto com label visível e estado de erro acessível.
 *
 * Quando `error` é informado, marca o campo com `aria-invalid`, associa a
 * mensagem via `aria-describedby` e aplica o estilo de borda de erro. A
 * mensagem fica fora do `<label>` para não poluir o nome acessível do campo.
 * Encaminha a `ref` para o `<input>` (foco no primeiro campo inválido).
 *
 * @param props - Propriedades do input, incluindo `id`, `label` e `error`.
 * @returns Campo de formulário acessível.
 */
export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { id, label, error, className = '', ...props },
  ref,
) {
  const temErro = Boolean(error)
  const erroId = `${id}-erro`
  return (
    <div className="rsp-field-wrap">
      <label className="rsp-field" htmlFor={id}>
        <span>{label}</span>
        <input
          ref={ref}
          id={id}
          className={`rsp-input ${temErro ? 'rsp-input--erro' : ''} ${className}`.trim()}
          aria-invalid={temErro || undefined}
          aria-describedby={temErro ? erroId : undefined}
          {...props}
        />
      </label>
      {temErro && (
        <span id={erroId} className="rsp-field__erro" role="alert">
          {error}
        </span>
      )}
    </div>
  )
})
