import { useRef, useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'
import { Button, Input } from '../components/ui'
import { useToast } from '../components/Toast'
import { Seo } from '../components/Seo'
import { formatarTelefone, isEmailValido, isTelefoneValido } from '../utils/format'
import type { RegistroPayload } from '../types/api'

type CamposCadastro = {
  nome: string
  email: string
  senha: string
  telefone: string
}

type ErrosCadastro = Partial<Record<keyof CamposCadastro | 'consentimento', string>>

const SENHA_MINIMA = 8

/**
 * Página de cadastro de protetor com validação inline e consentimento LGPD.
 *
 * @returns Formulário de criação de conta acessível.
 */
export function CadastroPage() {
  const { registrar } = useAuth()
  const { mostrar } = useToast()
  const navigate = useNavigate()

  const [campos, setCampos] = useState<CamposCadastro>({
    nome: '',
    email: '',
    senha: '',
    telefone: '',
  })
  const [consentimento, setConsentimento] = useState(false)
  const [erros, setErros] = useState<ErrosCadastro>({})
  const [erroGeral, setErroGeral] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  const nomeRef = useRef<HTMLInputElement>(null)
  const emailRef = useRef<HTMLInputElement>(null)
  const senhaRef = useRef<HTMLInputElement>(null)
  const telefoneRef = useRef<HTMLInputElement>(null)
  const consentimentoRef = useRef<HTMLInputElement>(null)

  function atualizar<K extends keyof CamposCadastro>(campo: K, valor: string) {
    const proximoValor = campo === 'telefone' ? formatarTelefone(valor) : valor
    setCampos((atual) => ({ ...atual, [campo]: proximoValor }))
    setErros((atual) => ({ ...atual, [campo]: undefined }))
  }

  function validar(): ErrosCadastro {
    const proximos: ErrosCadastro = {}
    if (campos.nome.trim().length < 2) {
      proximos.nome = 'Informe seu nome.'
    }
    if (!isEmailValido(campos.email)) {
      proximos.email = 'Informe um e-mail válido.'
    }
    if (campos.senha.length < SENHA_MINIMA) {
      proximos.senha = 'A senha deve ter pelo menos 8 caracteres.'
    }
    if (campos.telefone.trim() && !isTelefoneValido(campos.telefone)) {
      proximos.telefone = 'Informe um telefone válido com DDD.'
    }
    if (!consentimento) {
      proximos.consentimento = 'É necessário aceitar a política de privacidade.'
    }
    return proximos
  }

  function focarPrimeiroInvalido(proximos: ErrosCadastro) {
    if (proximos.nome) {
      nomeRef.current?.focus()
    } else if (proximos.email) {
      emailRef.current?.focus()
    } else if (proximos.senha) {
      senhaRef.current?.focus()
    } else if (proximos.telefone) {
      telefoneRef.current?.focus()
    } else if (proximos.consentimento) {
      consentimentoRef.current?.focus()
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
      const payload: RegistroPayload = {
        nome: campos.nome.trim(),
        email: campos.email.trim(),
        senha: campos.senha,
        consentimento_aceito: true,
      }
      if (campos.telefone.trim()) {
        payload.telefone = campos.telefone.trim()
      }
      await registrar(payload)
      mostrar('Conta criada. Bem-vindo(a) à Rede Solidária Pet!', 'sucesso')
      navigate('/pedidos', { replace: true })
    } catch (erro) {
      const status = (erro as { response?: { status?: number } })?.response?.status
      if (status === 409) {
        setErroGeral('Este e-mail já está cadastrado. Tente entrar.')
      } else {
        setErroGeral('Não foi possível criar sua conta. Tente novamente.')
      }
    } finally {
      setEnviando(false)
    }
  }

  return (
    <section className="rsp-page rsp-page--narrow rsp-formpage">
      <Seo title="Criar conta" description="Crie sua conta na Rede Solidária Pet." />
      <div className="rsp-page__header">
        <div>
          <p className="rsp-eyebrow">Acesso</p>
          <h1 className="rsp-page__title">Criar conta</h1>
          <p className="rsp-page__sub">
            Cadastre-se para publicar pedidos e coordenar ajudas para os animais.
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
          ref={nomeRef}
          id="nome"
          name="nome"
          label="Nome"
          autoComplete="name"
          value={campos.nome}
          onChange={(event) => atualizar('nome', event.target.value)}
          error={erros.nome}
          placeholder="Como podemos te chamar"
        />
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
          autoComplete="new-password"
          value={campos.senha}
          onChange={(event) => atualizar('senha', event.target.value)}
          error={erros.senha}
          placeholder="Mínimo de 8 caracteres"
        />
        <Input
          ref={telefoneRef}
          id="telefone"
          name="telefone"
          type="tel"
          label="Telefone (opcional)"
          autoComplete="tel"
          inputMode="numeric"
          value={campos.telefone}
          onChange={(event) => atualizar('telefone', event.target.value)}
          error={erros.telefone}
          placeholder="(11) 99999-0000"
        />
        <div className="rsp-field-wrap">
          <label className="rsp-checkbox" htmlFor="consentimento">
            <input
              ref={consentimentoRef}
              id="consentimento"
              type="checkbox"
              checked={consentimento}
              aria-invalid={erros.consentimento ? true : undefined}
              aria-describedby={erros.consentimento ? 'consentimento-erro' : undefined}
              onChange={(event) => {
                setConsentimento(event.target.checked)
                setErros((atual) => ({ ...atual, consentimento: undefined }))
              }}
            />
            <span>
              Aceito a <Link to="/privacidade">política de privacidade</Link> e o tratamento dos
              meus dados conforme a LGPD.
            </span>
          </label>
          {erros.consentimento && (
            <span id="consentimento-erro" className="rsp-field__erro" role="alert">
              {erros.consentimento}
            </span>
          )}
        </div>
        <Button type="submit" disabled={enviando}>
          {enviando ? 'Criando conta...' : 'Criar conta'}
        </Button>
        <p className="rsp-help">
          Já tem conta? <Link to="/entrar">Entrar</Link>
        </p>
      </form>
    </section>
  )
}
