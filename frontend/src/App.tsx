import { useRoutes } from 'react-router-dom'

import { routes } from './router'

/**
 * Componente raiz da aplicação Rede Solidária Pet.
 *
 * @returns Árvore React com as rotas da aplicação.
 */
export function App() {
  return useRoutes(routes)
}
