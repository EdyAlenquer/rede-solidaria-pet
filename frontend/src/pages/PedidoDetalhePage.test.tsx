import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HelmetProvider } from 'react-helmet-async'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { PedidoDetalhePage } from './PedidoDetalhePage'
import { criarAtendimento, listarAtendimentos } from '../services/api/atendimentos'
import { denunciarPedido } from '../services/api/denuncias'
import {
  alterarStatusPedido,
  excluirPedido,
  obterPedido,
  revelarContato,
} from '../services/api/pedidos'
import type { Pedido, UsuarioRead } from '../types/api'

vi.mock('../services/api/atendimentos', () => ({
  criarAtendimento: vi.fn(),
  listarAtendimentos: vi.fn(),
}))

vi.mock('../services/api/denuncias', () => ({
  denunciarPedido: vi.fn(),
}))

vi.mock('../services/api/pedidos', () => ({
  obterPedido: vi.fn(),
  revelarContato: vi.fn(),
  alterarStatusPedido: vi.fn(),
  excluirPedido: vi.fn(),
}))

// O mapa Leaflet não monta em jsdom: mocamos por um marcador estático.
vi.mock('../components/MapaPedidos', () => ({
  __esModule: true,
  default: ({ pontos }: { pontos: { id: number }[] }) => (
    <div data-testid="mock-mapa">mapa com {pontos.length} ponto(s)</div>
  ),
}))

const mostrarMock = vi.fn()
vi.mock('../components/Toast', () => ({
  useToast: () => ({ mostrar: mostrarMock }),
}))

let authState: { usuario: UsuarioRead | null; isAuthenticated: boolean }
vi.mock('../auth/AuthContext', () => ({
  useAuth: () => authState,
}))

const pedidoBase: Pedido = {
  id: 7,
  titulo: 'Gata precisa de transporte',
  descricao: 'Precisa ir até a clínica parceira para consulta.',
  categoria: 'transporte',
  urgencia: 'alta',
  status: 'aberto',
  data_criacao: '2026-05-27T12:00:00Z',
  cidade: 'São Paulo',
  estado: 'SP',
  especie: 'gato',
  porte: 'pequeno',
  latitude: -23.5,
  longitude: -46.6,
  imagens: [{ id: 1, url: '/uploads/gata.jpg', ordem: 0 }],
}

const autor: UsuarioRead = { id: 1, nome: 'Ana Autora', email: 'ana@x.com', papel: 'protetor' }

describe('PedidoDetalhePage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    authState = { usuario: null, isAuthenticated: false }
    vi.mocked(obterPedido).mockResolvedValue(pedidoBase)
    vi.mocked(listarAtendimentos).mockResolvedValue([
      {
        id: 3,
        pedido_id: 7,
        tipo_ajuda: 'transporte',
        observacao: 'Posso levar amanhã cedo.',
        data_contato: '2026-05-27T13:00:00Z',
      },
    ])
    vi.mocked(revelarContato).mockResolvedValue({
      contato: '11999990000',
      whatsapp: 'https://wa.me/5511999990000',
    })
    vi.mocked(criarAtendimento).mockResolvedValue({
      id: 12,
      pedido_id: 7,
      tipo_ajuda: 'racao',
      observacao: 'Consigo entregar hoje.',
      data_contato: '2026-05-27T14:00:00Z',
    })
    vi.mocked(alterarStatusPedido).mockResolvedValue({ ...pedidoBase, status: 'concluido' })
    vi.mocked(excluirPedido).mockResolvedValue(undefined)
    vi.mocked(denunciarPedido).mockResolvedValue(undefined)
  })

  function renderPage(initialEntries = ['/pedidos/7']) {
    render(
      <HelmetProvider>
        <MemoryRouter initialEntries={initialEntries}>
          <Routes>
            <Route path="/pedidos" element={<div>Lista de pedidos</div>} />
            <Route path="/pedidos/:pedidoId" element={<PedidoDetalhePage />} />
            <Route path="/pedidos/:pedidoId/editar" element={<div>Tela de edição</div>} />
            <Route path="/entrar" element={<div>Tela de login</div>} />
          </Routes>
        </MemoryRouter>
      </HelmetProvider>,
    )
  }

  it('mostra galeria real, badges, mini-mapa e histórico de atendimentos', async () => {
    renderPage()

    expect(await screen.findByRole('heading', { name: pedidoBase.titulo })).toBeInTheDocument()
    const figura = screen.getByRole('img', { name: /gata precisa de transporte/i })
    expect(figura).toHaveAttribute('src', '/uploads/gata.jpg')
    expect(figura).toHaveAttribute('loading', 'lazy')
    const caracteristicas = screen.getByRole('group', { name: /características do pedido/i })
    expect(within(caracteristicas).getByText('Transporte')).toBeInTheDocument()
    expect(within(caracteristicas).getByText('Urgente')).toBeInTheDocument()
    expect(within(caracteristicas).getByText('Gato')).toBeInTheDocument()
    // O mapa é carregado via React.lazy/Suspense; aguarde a resolução.
    expect(await screen.findByTestId('mock-mapa')).toBeInTheDocument()
    expect(screen.getByText(/Posso levar amanhã cedo/i)).toBeInTheDocument()
  })

  it('não chama a API quando o id da rota é inválido', async () => {
    renderPage(['/pedidos/abc'])

    expect(await screen.findByText(/pedido não encontrado/i)).toBeInTheDocument()
    expect(obterPedido).not.toHaveBeenCalled()
    expect(listarAtendimentos).not.toHaveBeenCalled()
  })

  it('exige login para revelar contato quando anônimo', async () => {
    renderPage()
    await screen.findByRole('heading', { name: pedidoBase.titulo })

    expect(
      screen.getByRole('link', { name: /entrar para ver o contato/i }),
    ).toHaveAttribute('href', '/entrar')
    expect(screen.queryByRole('button', { name: /revelar contato/i })).not.toBeInTheDocument()
  })

  it('revela contato e link de WhatsApp quando autenticado', async () => {
    authState = { usuario: { ...autor, id: 99 }, isAuthenticated: true }
    const user = userEvent.setup()
    renderPage()
    await screen.findByRole('heading', { name: pedidoBase.titulo })

    expect(screen.queryByText('11999990000')).not.toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /revelar contato/i }))

    expect(await screen.findByText('11999990000')).toBeInTheDocument()
    expect(revelarContato).toHaveBeenCalledWith(7)
    expect(screen.getByRole('link', { name: /whatsapp/i })).toHaveAttribute(
      'href',
      'https://wa.me/5511999990000',
    )
  })

  it('envia atendimento sem doador_id no fluxo "Quero ajudar" autenticado', async () => {
    authState = { usuario: { ...autor, id: 99 }, isAuthenticated: true }
    const user = userEvent.setup()
    renderPage()
    await screen.findByRole('heading', { name: pedidoBase.titulo })

    await user.click(screen.getByRole('button', { name: /quero ajudar/i }))
    await user.selectOptions(screen.getByLabelText('Tipo de ajuda'), 'racao')
    await user.type(screen.getByLabelText(/observação/i), 'Consigo entregar hoje.')
    await user.click(screen.getByRole('button', { name: /confirmar ajuda/i }))

    await waitFor(() =>
      expect(criarAtendimento).toHaveBeenCalledWith(7, {
        tipo_ajuda: 'racao',
        observacao: 'Consigo entregar hoje.',
      }),
    )
  })

  it('mostra CTA de login no lugar do formulário de ajuda quando anônimo', async () => {
    renderPage()
    await screen.findByRole('heading', { name: pedidoBase.titulo })

    expect(screen.getByRole('link', { name: /entrar para ajudar/i })).toHaveAttribute(
      'href',
      '/entrar',
    )
    expect(screen.queryByRole('button', { name: /quero ajudar/i })).not.toBeInTheDocument()
  })

  it('exibe ações de autor (editar/excluir) e exclui após confirmação', async () => {
    authState = { usuario: autor, isAuthenticated: true }
    vi.mocked(obterPedido).mockResolvedValue({ ...pedidoBase, autor_id: 1 } as Pedido)
    const user = userEvent.setup()
    renderPage()
    await screen.findByRole('heading', { name: pedidoBase.titulo })

    expect(screen.getByRole('link', { name: /editar/i })).toHaveAttribute(
      'href',
      '/pedidos/7/editar',
    )

    await user.click(screen.getByRole('button', { name: /excluir/i }))
    const dialog = await screen.findByRole('dialog')
    await user.click(within(dialog).getByRole('button', { name: /confirmar exclusão/i }))

    await waitFor(() => expect(excluirPedido).toHaveBeenCalledWith(7))
  })

  it('denuncia o pedido pelo modal quando autenticado', async () => {
    authState = { usuario: { ...autor, id: 99 }, isAuthenticated: true }
    const user = userEvent.setup()
    renderPage()
    await screen.findByRole('heading', { name: pedidoBase.titulo })

    await user.click(screen.getByRole('button', { name: /denunciar/i }))
    const dialog = await screen.findByRole('dialog')
    await user.selectOptions(within(dialog).getByLabelText(/motivo/i), 'golpe')
    await user.click(within(dialog).getByRole('button', { name: /enviar denúncia/i }))

    await waitFor(() =>
      expect(denunciarPedido).toHaveBeenCalledWith(7, expect.objectContaining({ motivo: 'golpe' })),
    )
  })
})
