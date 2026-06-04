import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { Modal } from './Modal'

describe('Modal', () => {
  it('não renderiza nada quando fechado', () => {
    render(
      <Modal open={false} onClose={vi.fn()} titulo="Confirmar">
        <p>conteúdo</p>
      </Modal>,
    )
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('renderiza com role=dialog, título acessível e conteúdo quando aberto', () => {
    render(
      <Modal open onClose={vi.fn()} titulo="Confirmar exclusão">
        <p>Tem certeza?</p>
      </Modal>,
    )
    const dialog = screen.getByRole('dialog')
    expect(dialog).toHaveAttribute('aria-modal', 'true')
    expect(dialog).toHaveAccessibleName('Confirmar exclusão')
    expect(screen.getByText('Tem certeza?')).toBeInTheDocument()
  })

  it('move o foco para dentro do diálogo ao abrir', () => {
    render(
      <Modal open onClose={vi.fn()} titulo="Confirmar">
        <button type="button">Confirmar agora</button>
      </Modal>,
    )
    const dialog = screen.getByRole('dialog')
    expect(dialog.contains(document.activeElement)).toBe(true)
  })

  it('fecha ao pressionar ESC', async () => {
    const onClose = vi.fn()
    const user = userEvent.setup()
    render(
      <Modal open onClose={onClose} titulo="Confirmar">
        <p>conteúdo</p>
      </Modal>,
    )
    await user.keyboard('{Escape}')
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('fecha ao acionar o botão de fechar', async () => {
    const onClose = vi.fn()
    const user = userEvent.setup()
    render(
      <Modal open onClose={onClose} titulo="Confirmar">
        <p>conteúdo</p>
      </Modal>,
    )
    await user.click(screen.getByRole('button', { name: /fechar/i }))
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('mantém o foco preso dentro do diálogo ao tabular', async () => {
    const user = userEvent.setup()
    render(
      <Modal open onClose={vi.fn()} titulo="Confirmar">
        <button type="button">Primeiro</button>
        <button type="button">Último</button>
      </Modal>,
    )
    const fechar = screen.getByRole('button', { name: /fechar/i })
    const ultimo = screen.getByRole('button', { name: 'Último' }) as HTMLButtonElement

    ultimo.focus()
    await user.tab()
    expect(document.activeElement).toBe(fechar)

    await user.tab({ shift: true })
    expect(document.activeElement).toBe(ultimo)
  })
})
