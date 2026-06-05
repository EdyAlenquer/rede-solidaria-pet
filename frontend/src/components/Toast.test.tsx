import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import { ToastProvider, useToast } from './Toast'

function Disparador() {
  const { mostrar } = useToast()
  return (
    <button type="button" onClick={() => mostrar('Ajuda registrada com sucesso.')}>
      avisar
    </button>
  )
}

describe('ToastProvider', () => {
  it('expõe uma região aria-live polite para feedback assistivo', () => {
    render(
      <ToastProvider>
        <Disparador />
      </ToastProvider>,
    )

    const regiao = screen.getByRole('status')
    expect(regiao).toHaveAttribute('aria-live', 'polite')
  })

  it('anuncia a mensagem ao chamar mostrar', async () => {
    const user = userEvent.setup()
    render(
      <ToastProvider>
        <Disparador />
      </ToastProvider>,
    )

    await user.click(screen.getByRole('button', { name: 'avisar' }))

    await waitFor(() =>
      expect(screen.getByText('Ajuda registrada com sucesso.')).toBeInTheDocument(),
    )
  })
})
