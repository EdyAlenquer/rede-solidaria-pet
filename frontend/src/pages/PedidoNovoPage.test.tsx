import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HelmetProvider } from 'react-helmet-async'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { PedidoNovoPage } from './PedidoNovoPage'
import { criarPedido } from '../services/api/pedidos'
import { enviarImagem } from '../services/api/imagens'
import { buscarEndereco, type ResultadoEndereco } from '../utils/geocoding'

vi.mock('../services/api/pedidos', () => ({
  criarPedido: vi.fn(),
}))

vi.mock('../services/api/imagens', () => ({
  enviarImagem: vi.fn(),
}))

vi.mock('../utils/geocoding', () => ({
  buscarEndereco: vi.fn(),
}))

const mostrarMock = vi.fn()
const navigateMock = vi.fn()

vi.mock('../components/Toast', () => ({
  useToast: () => ({ mostrar: mostrarMock }),
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return {
    ...actual,
    useNavigate: () => navigateMock,
  }
})

// O mapa Leaflet não monta em jsdom: mocamos por um botão que reporta um ponto.
vi.mock('../components/MapaSelecao', () => ({
  __esModule: true,
  default: ({ onSelecionar }: { onSelecionar: (c: { latitude: number; longitude: number }) => void }) => (
    <button type="button" onClick={() => onSelecionar({ latitude: -23.5, longitude: -46.6 })}>
      mock-mapa-selecionar
    </button>
  ),
}))

const enderecoExato: ResultadoEndereco = {
  label: 'Rua Augusta, Consolação, São Paulo, SP, Brasil',
  latitude: -23.55,
  longitude: -46.66,
  cidade: 'São Paulo',
  estado: 'SP',
  bairro: 'Consolação',
}

const pedidoCriado = {
  id: 22,
  titulo: 'Ração para filhotes',
  descricao: 'Família temporária precisa de ração hoje mesmo.',
  categoria: 'racao',
  urgencia: 'alta' as const,
  status: 'aberto' as const,
  data_criacao: '2026-05-27T12:00:00',
  cidade: 'São Paulo',
  estado: 'SP',
  imagens: [],
}

function renderPage() {
  render(
    <HelmetProvider>
      <MemoryRouter initialEntries={['/pedidos/novo']}>
        <PedidoNovoPage />
      </MemoryRouter>
    </HelmetProvider>,
  )
}

async function preencherObrigatorios(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText('Título do pedido'), 'Ração para filhotes')
  await user.type(
    screen.getByLabelText(/Descrição/),
    'Família temporária precisa de ração hoje mesmo.',
  )
  await user.selectOptions(screen.getByLabelText('Categoria'), 'racao')
  await user.selectOptions(screen.getByLabelText('Urgência'), 'alta')
  await user.type(screen.getByLabelText('Contato'), '11999990000')
  await user.type(screen.getByLabelText('Cidade'), 'São Paulo')
  await user.selectOptions(screen.getByLabelText('Estado'), 'SP')
  await user.click(screen.getByLabelText(/aceito a política de privacidade/i))
}

describe('PedidoNovoPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(criarPedido).mockResolvedValue(pedidoCriado)
    vi.mocked(enviarImagem).mockResolvedValue({ id: 1, url: '/uploads/a.jpg', ordem: 0 })
    vi.mocked(buscarEndereco).mockResolvedValue([enderecoExato])
  })

  it('mostra validações em PT-BR para envio vazio e não chama a API', async () => {
    const user = userEvent.setup()
    renderPage()

    await user.click(screen.getByRole('button', { name: /publicar pedido/i }))

    expect(screen.getByText('Informe um título com pelo menos 3 caracteres.')).toBeInTheDocument()
    expect(screen.getByText('Informe uma descrição com pelo menos 10 caracteres.')).toBeInTheDocument()
    expect(screen.getByText('Selecione uma categoria.')).toBeInTheDocument()
    expect(screen.getByText('Informe a cidade.')).toBeInTheDocument()
    expect(screen.getByText('Selecione o estado.')).toBeInTheDocument()
    expect(screen.getByText('É necessário aceitar a política de privacidade.')).toBeInTheDocument()
    expect(criarPedido).not.toHaveBeenCalled()
  })

  it('exige consentimento antes de enviar', async () => {
    const user = userEvent.setup()
    renderPage()

    await user.type(screen.getByLabelText('Título do pedido'), 'Ração para filhotes')
    await user.type(
      screen.getByLabelText(/Descrição/),
      'Família temporária precisa de ração hoje mesmo.',
    )
    await user.selectOptions(screen.getByLabelText('Categoria'), 'racao')
    await user.type(screen.getByLabelText('Contato'), '11999990000')
    await user.type(screen.getByLabelText('Cidade'), 'São Paulo')
    await user.selectOptions(screen.getByLabelText('Estado'), 'SP')
    await user.click(screen.getByRole('button', { name: /publicar pedido/i }))

    expect(screen.getByText('É necessário aceitar a política de privacidade.')).toBeInTheDocument()
    expect(criarPedido).not.toHaveBeenCalled()
  })

  it('envia payload válido com consentimento e navega para o detalhe', async () => {
    const user = userEvent.setup()
    renderPage()

    await preencherObrigatorios(user)
    await user.click(screen.getByRole('button', { name: /publicar pedido/i }))

    await waitFor(() =>
      expect(criarPedido).toHaveBeenCalledWith(
        expect.objectContaining({
          titulo: 'Ração para filhotes',
          descricao: 'Família temporária precisa de ração hoje mesmo.',
          categoria: 'racao',
          urgencia: 'alta',
          contato: '11999990000',
          cidade: 'São Paulo',
          estado: 'SP',
          consentimento_aceito: true,
        }),
      ),
    )
    expect(navigateMock).toHaveBeenCalledWith('/pedidos/22')
    expect(mostrarMock).toHaveBeenCalled()
  })

  it('inclui a localização escolhida no mapa', async () => {
    const user = userEvent.setup()
    renderPage()

    await preencherObrigatorios(user)
    await user.click(screen.getByRole('button', { name: 'mock-mapa-selecionar' }))
    await user.click(screen.getByRole('button', { name: /publicar pedido/i }))

    await waitFor(() =>
      expect(criarPedido).toHaveBeenCalledWith(
        expect.objectContaining({ latitude: -23.5, longitude: -46.6 }),
      ),
    )
  })

  it('busca um endereço, autopreenche cidade/estado/bairro e fixa a coordenada', async () => {
    const user = userEvent.setup()
    renderPage()

    await user.type(screen.getByLabelText(/^Endereço/i), 'rua augusta')

    const opcao = await screen.findByRole('option', {
      name: 'Rua Augusta, Consolação, São Paulo, SP, Brasil',
    })
    await user.click(opcao)

    // Autopreenche os campos a partir do endereço exato escolhido.
    expect(screen.getByLabelText('Cidade')).toHaveValue('São Paulo')
    expect(screen.getByLabelText('Estado')).toHaveValue('SP')
    expect(screen.getByLabelText('Bairro (opcional)')).toHaveValue('Consolação')

    // Preenche os demais obrigatórios e envia: a coordenada do endereço vai junto.
    await user.type(screen.getByLabelText('Título do pedido'), 'Ração para filhotes')
    await user.type(
      screen.getByLabelText(/Descrição/),
      'Família temporária precisa de ração hoje mesmo.',
    )
    await user.selectOptions(screen.getByLabelText('Categoria'), 'racao')
    await user.type(screen.getByLabelText('Contato'), '11999990000')
    await user.click(screen.getByLabelText(/aceito a política de privacidade/i))
    await user.click(screen.getByRole('button', { name: /publicar pedido/i }))

    await waitFor(() =>
      expect(criarPedido).toHaveBeenCalledWith(
        expect.objectContaining({
          cidade: 'São Paulo',
          estado: 'SP',
          bairro: 'Consolação',
          latitude: -23.55,
          longitude: -46.66,
        }),
      ),
    )
  })

  it('mostra erro quando a criação do pedido falha', async () => {
    const user = userEvent.setup()
    vi.mocked(criarPedido).mockRejectedValue(new Error('500'))
    renderPage()

    await preencherObrigatorios(user)
    await user.click(screen.getByRole('button', { name: /publicar pedido/i }))

    expect(
      await screen.findByText('Não foi possível publicar o pedido. Tente novamente.'),
    ).toBeInTheDocument()
    expect(navigateMock).not.toHaveBeenCalled()
  })
})
