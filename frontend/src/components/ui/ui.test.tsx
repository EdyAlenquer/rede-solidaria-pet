import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { Badge, Button, Card, Input, Select } from '.'

describe('componentes base', () => {
  it('renderiza botão com nome acessível', () => {
    render(<Button>Salvar pedido</Button>)

    expect(screen.getByRole('button', { name: /salvar pedido/i })).toBeInTheDocument()
  })

  it('associa input ao label visível', () => {
    render(<Input id="bairro" label="Bairro" placeholder="Vila Esperança" />)

    expect(screen.getByLabelText('Bairro')).toHaveAttribute('placeholder', 'Vila Esperança')
  })

  it('associa select ao label e opções', () => {
    render(
      <Select
        id="urgencia"
        label="Urgência"
        options={[
          { label: 'Alta', value: 'alta' },
          { label: 'Média', value: 'media' },
        ]}
      />,
    )

    expect(screen.getByLabelText('Urgência')).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Alta' })).toBeInTheDocument()
  })

  it('renderiza card como região nomeada', () => {
    render(
      <Card title="Pedido em destaque">
        <p>Precisa de ração hoje.</p>
      </Card>,
    )

    expect(screen.getByRole('region', { name: 'Pedido em destaque' })).toBeInTheDocument()
  })

  it('renderiza badge com texto de status', () => {
    render(<Badge tone="warning">Urgente</Badge>)

    expect(screen.getByText('Urgente')).toBeInTheDocument()
  })
})
