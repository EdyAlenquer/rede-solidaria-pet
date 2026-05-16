import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'

import { App } from './App'

describe('App', () => {
  it('renderiza o título principal da aplicação', () => {
    render(<App />)

    expect(
      screen.getByRole('heading', { level: 1, name: /rede solidária pet/i }),
    ).toBeInTheDocument()
  })
})
