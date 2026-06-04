import type { RouteObject } from 'react-router-dom'

import { RotaProtegida } from './auth/RotaProtegida'
import { ErrorBoundary } from './components/ErrorBoundary'
import { AppLayout } from './components/layout/AppLayout'
import { CadastroPage } from './pages/CadastroPage'
import { ContatoPage } from './pages/ContatoPage'
import { FaqPage } from './pages/FaqPage'
import { HomePage } from './pages/HomePage'
import { LoginPage } from './pages/LoginPage'
import { MapaPage } from './pages/MapaPage'
import { NotFoundPage } from './pages/NotFoundPage'
import { PedidoDetalhePage } from './pages/PedidoDetalhePage'
import { PedidoEditarPage } from './pages/PedidoEditarPage'
import { PedidoListaPage } from './pages/PedidoListaPage'
import { PedidoNovoPage } from './pages/PedidoNovoPage'
import { PerfilPage } from './pages/PerfilPage'
import { PlaygroundPage } from './pages/PlaygroundPage'
import { PrivacidadePage } from './pages/PrivacidadePage'
import { SobrePage } from './pages/SobrePage'
import { TermosPage } from './pages/TermosPage'

const childRoutes: RouteObject[] = [
  { path: '/', element: <HomePage /> },
  { path: '/pedidos', element: <PedidoListaPage /> },
  { path: '/pedidos/mapa', element: <MapaPage /> },
  { path: '/pedidos/:pedidoId', element: <PedidoDetalhePage /> },
  { path: '/entrar', element: <LoginPage /> },
  { path: '/cadastrar', element: <CadastroPage /> },
  {
    element: <RotaProtegida />,
    children: [
      { path: '/pedidos/novo', element: <PedidoNovoPage /> },
      { path: '/pedidos/:pedidoId/editar', element: <PedidoEditarPage /> },
      { path: '/perfil', element: <PerfilPage /> },
    ],
  },
  { path: '/termos', element: <TermosPage /> },
  { path: '/privacidade', element: <PrivacidadePage /> },
  { path: '/sobre', element: <SobrePage /> },
  { path: '/contato', element: <ContatoPage /> },
  { path: '/faq', element: <FaqPage /> },
]

// O playground de componentes só existe em desenvolvimento. Em produção,
// `import.meta.env.DEV` é substituído por `false` no build, então este bloco
// (e o `PlaygroundPage` referenciado apenas aqui) é eliminado por tree-shaking.
if (import.meta.env.DEV) {
  childRoutes.push({ path: '/__playground__', element: <PlaygroundPage /> })
}

childRoutes.push({ path: '*', element: <NotFoundPage /> })

/**
 * Rotas client-side da aplicação.
 *
 * @returns Configuração consumida por `useRoutes`.
 */
export const routes: RouteObject[] = [
  {
    element: (
      <ErrorBoundary>
        <AppLayout />
      </ErrorBoundary>
    ),
    children: childRoutes,
  },
]
