import { forwardRef, type SelectHTMLAttributes } from 'react'

type SelectOption = {
  label: string
  value: string
}

type SelectProps = SelectHTMLAttributes<HTMLSelectElement> & {
  id: string
  label: string
  options: SelectOption[]
  /** Mensagem de erro a exibir abaixo do campo (ativa o estado inválido). */
  error?: string | null
}

/**
 * Select base com label visível e estado de erro acessível.
 *
 * Quando `error` é informado, marca o campo com `aria-invalid`, associa a
 * mensagem via `aria-describedby` e aplica o estilo de borda de erro. A
 * mensagem fica fora do `<label>` para não poluir o nome acessível do campo.
 * Encaminha a `ref` para o `<select>` (foco no primeiro campo inválido).
 *
 * @param props - Propriedades do select, opções e `error`.
 * @returns Campo select acessível.
 */
export const Select = forwardRef<HTMLSelectElement, SelectProps>(function Select(
  { id, label, options, error, className = '', ...props },
  ref,
) {
  const temErro = Boolean(error)
  const erroId = `${id}-erro`
  return (
    <div className="rsp-field-wrap">
      <label className="rsp-field" htmlFor={id}>
        <span>{label}</span>
        <select
          ref={ref}
          id={id}
          className={`rsp-input rsp-select ${temErro ? 'rsp-input--erro' : ''} ${className}`.trim()}
          aria-invalid={temErro || undefined}
          aria-describedby={temErro ? erroId : undefined}
          {...props}
        >
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>
      {temErro && (
        <span id={erroId} className="rsp-field__erro" role="alert">
          {error}
        </span>
      )}
    </div>
  )
})
