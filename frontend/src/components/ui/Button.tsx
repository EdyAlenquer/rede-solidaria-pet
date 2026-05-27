import type { ButtonHTMLAttributes, ReactNode } from 'react'

type ButtonVariant = 'primary' | 'secondary' | 'ghost'

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode
  variant?: ButtonVariant
}

/**
 * Botão base da interface.
 *
 * @param props - Propriedades nativas de botão e variante visual.
 * @returns Botão estilizado e acessível.
 */
export function Button({ children, className = '', variant = 'primary', ...props }: ButtonProps) {
  return (
    <button className={`rsp-btn rsp-btn--${variant} ${className}`.trim()} type="button" {...props}>
      {children}
    </button>
  )
}
