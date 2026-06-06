import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { CampoEndereco } from './CampoEndereco'
import { buscarEndereco, type ResultadoEndereco } from '../utils/geocoding'

vi.mock('../utils/geocoding', () => ({
  buscarEndereco: vi.fn(),
}))

const resultado: ResultadoEndereco = {
  label: 'Praça da Sé, Sé, São Paulo, SP, Brasil',
  latitude: -23.5503,
  longitude: -46.6339,
  cidade: 'São Paulo',
  estado: 'SP',
  bairro: 'Sé',
}

describe('CampoEndereco', () => {
  beforeEach(() => {
    vi.mocked(buscarEndereco).mockResolvedValue([resultado])
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('tem input acessível com label e dica em PT-BR', () => {
    render(<CampoEndereco onSelecionar={vi.fn()} />)

    expect(screen.getByLabelText(/Endereço/i)).toBeInTheDocument()
    expect(screen.getByText(/digite e selecione para marcar no mapa/i)).toBeInTheDocument()
  })

  it('busca após debounce e lista as sugestões como opções', async () => {
    const user = userEvent.setup()
    render(<CampoEndereco onSelecionar={vi.fn()} />)

    await user.type(screen.getByLabelText(/Endereço/i), 'praça da sé')

    await waitFor(() => expect(buscarEndereco).toHaveBeenCalledWith('praça da sé'))

    const opcoes = await screen.findAllByRole('option')
    expect(opcoes).toHaveLength(1)
    expect(opcoes[0]).toHaveTextContent('Praça da Sé, Sé, São Paulo, SP, Brasil')
  })

  it('não busca enquanto o termo tem menos de 3 caracteres', async () => {
    const user = userEvent.setup()
    render(<CampoEndereco onSelecionar={vi.fn()} />)

    await user.type(screen.getByLabelText(/Endereço/i), 'sé')
    // Espera além do debounce para garantir que nada foi buscado.
    await new Promise((resolve) => setTimeout(resolve, 600))

    expect(buscarEndereco).not.toHaveBeenCalled()
  })

  it('chama onSelecionar com o resultado ao clicar numa sugestão', async () => {
    const user = userEvent.setup()
    const onSelecionar = vi.fn()
    render(<CampoEndereco onSelecionar={onSelecionar} />)

    await user.type(screen.getByLabelText(/Endereço/i), 'praça da sé')

    const opcao = await screen.findByRole('option')
    await user.click(opcao)

    expect(onSelecionar).toHaveBeenCalledWith(resultado)
    // A lista fecha após a seleção.
    expect(screen.queryByRole('option')).not.toBeInTheDocument()
  })

  it('seleciona pela navegação por teclado (setas + Enter)', async () => {
    const user = userEvent.setup()
    const onSelecionar = vi.fn()
    render(<CampoEndereco onSelecionar={onSelecionar} />)

    const input = screen.getByLabelText(/Endereço/i)
    await user.type(input, 'praça da sé')
    await screen.findByRole('option')

    await user.keyboard('{ArrowDown}')
    await user.keyboard('{Enter}')

    expect(onSelecionar).toHaveBeenCalledWith(resultado)
  })

  it('mostra estado de carregando enquanto busca', async () => {
    let liberar: (valor: ResultadoEndereco[]) => void = () => {}
    vi.mocked(buscarEndereco).mockImplementation(
      () =>
        new Promise((resolve) => {
          liberar = resolve
        }),
    )
    const user = userEvent.setup()
    render(<CampoEndereco onSelecionar={vi.fn()} />)

    await user.type(screen.getByLabelText(/Endereço/i), 'praça da sé')

    expect(await screen.findByText(/Buscando endereços/i)).toBeInTheDocument()

    liberar([resultado])
    await screen.findByRole('option')
  })

  it('mostra mensagem de sem resultados quando a busca volta vazia', async () => {
    vi.mocked(buscarEndereco).mockResolvedValue([])
    const user = userEvent.setup()
    render(<CampoEndereco onSelecionar={vi.fn()} />)

    await user.type(screen.getByLabelText(/Endereço/i), 'endereço inexistente')

    expect(await screen.findByText(/Nenhum endereço encontrado/i)).toBeInTheDocument()
  })
})
