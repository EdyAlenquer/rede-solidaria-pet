import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import { login as loginRequest, me as meRequest, registrar as registrarRequest } from '../services/api/auth'
import { lerToken, salvarToken } from '../services/api/client'
import type { LoginPayload, RegistroPayload, UsuarioRead } from '../types/api'

type AuthContextValue = {
  /** Usuário autenticado, ou `null` quando anônimo. */
  usuario: UsuarioRead | null
  /** Verdadeiro enquanto a sessão inicial está sendo resolvida. */
  isLoading: boolean
  /** Verdadeiro quando há usuário autenticado. */
  isAuthenticated: boolean
  /** Autentica e carrega o usuário atual. */
  login: (payload: LoginPayload) => Promise<void>
  /** Registra um novo usuário e já autentica em seguida. */
  registrar: (payload: RegistroPayload) => Promise<void>
  /** Encerra a sessão, limpando token e usuário. */
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

type AuthProviderProps = {
  children: ReactNode
}

/**
 * Provedor de autenticação baseado em JWT persistido no `localStorage`.
 *
 * Ao montar, tenta resolver o usuário atual quando há token salvo. Expõe
 * `login`, `registrar`, `logout` e o estado de carregamento da sessão.
 *
 * @param props - Filhos que terão acesso ao contexto.
 * @returns Provedor React do contexto de autenticação.
 */
export function AuthProvider({ children }: AuthProviderProps) {
  const [usuario, setUsuario] = useState<UsuarioRead | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let ativo = true
    const token = lerToken()
    if (!token) {
      setIsLoading(false)
      return
    }
    meRequest()
      .then((atual) => {
        if (ativo) {
          setUsuario(atual)
        }
      })
      .catch(() => {
        salvarToken(null)
        if (ativo) {
          setUsuario(null)
        }
      })
      .finally(() => {
        if (ativo) {
          setIsLoading(false)
        }
      })
    return () => {
      ativo = false
    }
  }, [])

  const login = useCallback(async (payload: LoginPayload) => {
    const { access_token } = await loginRequest(payload)
    salvarToken(access_token)
    const atual = await meRequest()
    setUsuario(atual)
  }, [])

  const registrar = useCallback(
    async (payload: RegistroPayload) => {
      await registrarRequest(payload)
      await login({ email: payload.email, senha: payload.senha })
    },
    [login],
  )

  const logout = useCallback(() => {
    salvarToken(null)
    setUsuario(null)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      usuario,
      isLoading,
      isAuthenticated: usuario !== null,
      login,
      registrar,
      logout,
    }),
    [usuario, isLoading, login, registrar, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

/**
 * Acessa o contexto de autenticação.
 *
 * @returns Valor do contexto de autenticação.
 * @throws Error quando usado fora de um `AuthProvider`.
 */
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (context === null) {
    throw new Error('useAuth deve ser usado dentro de um AuthProvider.')
  }
  return context
}
