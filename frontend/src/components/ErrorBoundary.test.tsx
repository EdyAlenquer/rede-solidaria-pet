import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ErrorBoundary } from './ErrorBoundary'

function Explode(): JSX.Element {
  throw new Error('falha proposital')
}

describe('ErrorBoundary', () => {
  beforeEach(() => {
    vi.spyOn(console, 'error').mockImplementation(() => undefined)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('mostra um fallback amigável em PT-BR quando um filho quebra', () => {
    render(
      <ErrorBoundary>
        <Explode />
      </ErrorBoundary>,
    )

    expect(screen.getByText(/algo deu errado/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /tentar novamente/i })).toBeInTheDocument()
  })

  it('reseta e volta a renderizar os filhos ao tentar novamente', async () => {
    const user = userEvent.setup()

    function Alternavel() {
      const [quebrar, setQuebrar] = useState(true)
      return (
        <ErrorBoundary onReset={() => setQuebrar(false)}>
          {quebrar ? <Explode /> : <p>conteúdo recuperado</p>}
        </ErrorBoundary>
      )
    }

    render(<Alternavel />)
    await user.click(screen.getByRole('button', { name: /tentar novamente/i }))

    expect(screen.getByText('conteúdo recuperado')).toBeInTheDocument()
  })
})
