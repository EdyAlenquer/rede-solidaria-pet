import type { RouteObject } from 'react-router-dom'

import { AppLayout } from './components/layout/AppLayout'
import { HomePage } from './pages/HomePage'
import { PedidoDetalhePage } from './pages/PedidoDetalhePage'
import { PedidoListaPage } from './pages/PedidoListaPage'
import { PedidoNovoPage } from './pages/PedidoNovoPage'
import { PlaygroundPage } from './pages/PlaygroundPage'

/**
 * Rotas client-side da aplicação.
 *
 * @returns Configuração consumida por `useRoutes`.
 */
export const routes: RouteObject[] = [
  {
    element: <AppLayout />,
    children: [
      { path: '/', element: <HomePage /> },
      { path: '/pedidos', element: <PedidoListaPage /> },
      { path: '/pedidos/novo', element: <PedidoNovoPage /> },
      { path: '/pedidos/:pedidoId', element: <PedidoDetalhePage /> },
      { path: '/__playground__', element: <PlaygroundPage /> },
    ],
  },
]
