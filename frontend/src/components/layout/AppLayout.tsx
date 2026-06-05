import { useEffect, useRef } from 'react'
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../../auth/AuthContext'
import { Seo } from '../Seo'

/**
 * Layout base responsivo compartilhado pelas páginas.
 *
 * Inclui skip-link para o conteúdo, gestão de foco ao trocar de rota
 * (move o foco para `<main>`), navegação com ações de autenticação e rodapé
 * com links legais. Aplica também o SEO padrão da aplicação.
 *
 * @returns Estrutura com cabeçalho, conteúdo principal e rodapé.
 */
export function AppLayout() {
  const { isAuthenticated, usuario, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const mainRef = useRef<HTMLElement>(null)

  // Acessibilidade: a cada navegação, move o foco para o conteúdo principal
  // para que leitores de tela anunciem a nova página.
  useEffect(() => {
    mainRef.current?.focus()
  }, [location.pathname])

  function handleLogout() {
    logout()
    navigate('/')
  }

  return (
    <div className="rsp-app">
      <Seo />
      <a className="rsp-skip-link" href="#conteudo">
        Pular para o conteúdo
      </a>
      <header className="rsp-webheader">
        <NavLink to="/" className="rsp-logo" aria-label="Rede Solidária Pet">
          <span className="rsp-logo-mark" aria-hidden="true">
            ♡
          </span>
          <span>Rede Solidária Pet</span>
        </NavLink>
        <nav className="rsp-webheader__tabs" aria-label="Navegação principal">
          <NavLink to="/" end className="rsp-webtab">
            Início
          </NavLink>
          <NavLink to="/pedidos" className="rsp-webtab">
            Pedidos
          </NavLink>
          <NavLink to="/pedidos/mapa" className="rsp-webtab">
            Mapa
          </NavLink>
        </nav>
        <div className="rsp-webheader__actions">
          {isAuthenticated ? (
            <>
              <NavLink to="/perfil" className="rsp-webtab">
                {usuario ? usuario.nome.split(' ')[0] : 'Perfil'}
              </NavLink>
              <button type="button" className="rsp-btn rsp-btn--secondary" onClick={handleLogout}>
                Sair
              </button>
            </>
          ) : (
            <>
              <NavLink to="/entrar" className="rsp-webtab">
                Entrar
              </NavLink>
              <NavLink to="/cadastrar" className="rsp-btn rsp-btn--secondary">
                Cadastrar
              </NavLink>
            </>
          )}
          <NavLink to="/pedidos/novo" className="rsp-btn rsp-btn--primary">
            <span aria-hidden="true">+</span>
            Novo pedido
          </NavLink>
        </div>
      </header>
      <main id="conteudo" tabIndex={-1} ref={mainRef}>
        <Outlet />
      </main>
      <footer className="rsp-footer">
        <div className="rsp-footer__brand">
          <span>Rede Solidária Pet</span>
          <span>Ajuda comunitária para protetores, ONGs e voluntários.</span>
        </div>
        <nav className="rsp-footer__links" aria-label="Links institucionais">
          <Link to="/sobre">Sobre</Link>
          <Link to="/contato">Contato</Link>
          <Link to="/faq">FAQ</Link>
          <Link to="/termos">Termos de uso</Link>
          <Link to="/privacidade">Privacidade</Link>
        </nav>
      </footer>
    </div>
  )
}
