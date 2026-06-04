import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { useAuth } from './AuthContext'

/**
 * Guarda de rota que exige autenticação.
 *
 * Enquanto a sessão é resolvida, exibe um indicador acessível. Quando o usuário
 * não está autenticado, redireciona para `/entrar` preservando o destino
 * original em `state.from` para retorno após o login.
 *
 * @returns As rotas filhas, um indicador de carregamento ou um redirecionamento.
 */
export function RotaProtegida() {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <section className="rsp-page">
        <div className="rsp-skeleton" role="status">
          Verificando sua sessão...
        </div>
      </section>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/entrar" replace state={{ from: location }} />
  }

  return <Outlet />
}
