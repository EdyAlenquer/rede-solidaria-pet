import { useRef, useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'
import { Button, Input } from '../components/ui'
import { useToast } from '../components/Toast'
import { Seo } from '../components/Seo'
import { isEmailValido } from '../utils/format'

type CamposLogin = {
  email: string
  senha: string
}

type ErrosLogin = Partial<Record<keyof CamposLogin, string>>

type LocationState = {
  from?: { pathname?: string }
}

/**
 * Resolve o destino pós-login a partir do `state.from` da rota.
 *
 * @param state - Estado da navegação (pode conter a rota de origem).
 * @returns Caminho para redirecionar após autenticar.
 */
function destinoPosLogin(state: unknown): string {
  const from = (state as LocationState | null)?.from?.pathname
  return from && from !== '/entrar' ? from : '/pedidos'
}

/**
 * Página de login com validação inline e integração ao contexto de auth.
 *
 * @returns Formulário de entrada acessível.
 */
export function LoginPage() {
  const { login } = useAuth()
  const { mostrar } = useToast()
  const navigate = useNavigate()
  const location = useLocation()

  const [campos, setCampos] = useState<CamposLogin>({ email: '', senha: '' })
  const [erros, setErros] = useState<ErrosLogin>({})
  const [erroGeral, setErroGeral] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  const emailRef = useRef<HTMLInputElement>(null)
  const senhaRef = useRef<HTMLInputElement>(null)

  function atualizar<K extends keyof CamposLogin>(campo: K, valor: string) {
    setCampos((atual) => ({ ...atual, [campo]: valor }))
    setErros((atual) => ({ ...atual, [campo]: undefined }))
  }

  function validar(): ErrosLogin {
    const proximos: ErrosLogin = {}
    if (!isEmailValido(campos.email)) {
      proximos.email = 'Informe um e-mail válido.'
    }
    if (campos.senha.length === 0) {
      proximos.senha = 'Informe sua senha.'
    }
    return proximos
  }

  function focarPrimeiroInvalido(proximos: ErrosLogin) {
    if (proximos.email) {
      emailRef.current?.focus()
    } else if (proximos.senha) {
      senhaRef.current?.focus()
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErroGeral(null)
    const proximos = validar()
    setErros(proximos)
    if (Object.keys(proximos).length > 0) {
      focarPrimeiroInvalido(proximos)
      return
    }
    setEnviando(true)
    try {
      await login({ email: campos.email.trim(), senha: campos.senha })
      mostrar('Que bom ter você de volta!', 'sucesso')
      navigate(destinoPosLogin(location.state), { replace: true })
    } catch {
      setErroGeral('E-mail ou senha inválidos.')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <section className="rsp-page rsp-page--narrow rsp-formpage">
      <Seo title="Entrar" description="Acesse sua conta na Rede Solidária Pet." />
      <div className="rsp-page__header">
        <div>
          <p className="rsp-eyebrow">Acesso</p>
          <h1 className="rsp-page__title">Entrar</h1>
          <p className="rsp-page__sub">
            Acesse sua conta para publicar pedidos e acompanhar ajudas.
          </p>
        </div>
      </div>

      <form className="rsp-card rsp-form" onSubmit={handleSubmit} noValidate>
        {erroGeral && (
          <div className="rsp-alert" role="alert">
            <p>{erroGeral}</p>
          </div>
        )}
        <Input
          ref={emailRef}
          id="email"
          name="email"
          type="email"
          label="E-mail"
          autoComplete="email"
          value={campos.email}
          onChange={(event) => atualizar('email', event.target.value)}
          error={erros.email}
          placeholder="voce@exemplo.com"
        />
        <Input
          ref={senhaRef}
          id="senha"
          name="senha"
          type="password"
          label="Senha"
          autoComplete="current-password"
          value={campos.senha}
          onChange={(event) => atualizar('senha', event.target.value)}
          error={erros.senha}
        />
        <Button type="submit" disabled={enviando}>
          {enviando ? 'Entrando...' : 'Entrar'}
        </Button>
        <p className="rsp-help">
          Ainda não tem conta? <Link to="/cadastrar">Criar conta</Link>
        </p>
      </form>
    </section>
  )
}
