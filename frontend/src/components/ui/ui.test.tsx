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

  it('marca input inválido e descreve o erro', () => {
    render(<Input id="email" label="E-mail" error="Informe um e-mail válido." />)

    const campo = screen.getByLabelText('E-mail')
    expect(campo).toHaveAttribute('aria-invalid', 'true')
    expect(campo).toHaveAttribute('aria-describedby', 'email-erro')
    const mensagem = screen.getByText('Informe um e-mail válido.')
    expect(mensagem).toHaveAttribute('id', 'email-erro')
  })

  it('não marca input como inválido sem erro', () => {
    render(<Input id="bairro" label="Bairro" />)

    expect(screen.getByLabelText('Bairro')).not.toHaveAttribute('aria-invalid')
  })

  it('marca select inválido e descreve o erro', () => {
    render(
      <Select
        id="categoria"
        label="Categoria"
        error="Selecione uma categoria."
        options={[{ label: 'Ração', value: 'racao' }]}
      />,
    )

    const campo = screen.getByLabelText('Categoria')
    expect(campo).toHaveAttribute('aria-invalid', 'true')
    expect(campo).toHaveAttribute('aria-describedby', 'categoria-erro')
    expect(screen.getByText('Selecione uma categoria.')).toHaveAttribute('id', 'categoria-erro')
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
