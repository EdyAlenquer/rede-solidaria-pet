import type { InputHTMLAttributes } from 'react'

type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  id: string
  label: string
}

/**
 * Campo de texto com label visível.
 *
 * @param props - Propriedades do input, incluindo `id` e `label`.
 * @returns Campo de formulário acessível.
 */
export function Input({ id, label, className = '', ...props }: InputProps) {
  return (
    <label className="rsp-field" htmlFor={id}>
      <span>{label}</span>
      <input id={id} className={`rsp-input ${className}`.trim()} {...props} />
    </label>
  )
}
