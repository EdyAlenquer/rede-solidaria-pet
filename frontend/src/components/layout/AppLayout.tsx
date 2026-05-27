import { NavLink, Outlet } from 'react-router-dom'

/**
 * Layout base responsivo compartilhado pelas páginas.
 *
 * @returns Estrutura com cabeçalho, conteúdo principal e rodapé.
 */
export function AppLayout() {
  return (
    <div className="rsp-app">
      <header className="rsp-webheader">
        <NavLink to="/" className="rsp-logo" aria-label="Rede Solidária Pet">
          <span className="rsp-logo-mark" aria-hidden="true">
            ♡
          </span>
          <span>Rede Solidária Pet</span>
        </NavLink>
        <nav className="rsp-webheader__tabs" aria-label="Navegação principal">
          <NavLink to="/pedidos" className="rsp-webtab">
            Pedidos
          </NavLink>
          <NavLink to="/__playground__" className="rsp-webtab">
            Componentes
          </NavLink>
        </nav>
        <NavLink to="/pedidos/novo" className="rsp-btn rsp-btn--primary">
          <span aria-hidden="true">+</span>
          Novo pedido
        </NavLink>
      </header>
      <main>
        <Outlet />
      </main>
      <footer className="rsp-footer">
        <span>Rede Solidária Pet</span>
        <span>Ajuda comunitária para protetores, ONGs e voluntários.</span>
      </footer>
    </div>
  )
}
