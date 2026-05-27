import type { SelectHTMLAttributes } from 'react'

type SelectOption = {
  label: string
  value: string
}

type SelectProps = SelectHTMLAttributes<HTMLSelectElement> & {
  id: string
  label: string
  options: SelectOption[]
}

/**
 * Select base com label visível.
 *
 * @param props - Propriedades do select e opções renderizadas.
 * @returns Campo select acessível.
 */
export function Select({ id, label, options, className = '', ...props }: SelectProps) {
  return (
    <label className="rsp-field" htmlFor={id}>
      <span>{label}</span>
      <select id={id} className={`rsp-input rsp-select ${className}`.trim()} {...props}>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  )
}
