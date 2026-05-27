import type { FormEvent } from 'react'
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

/**
 * Página de detalhe de pedido com histórico e fluxo de ajuda.
 *
 * @returns Tela de detalhe integrada à API.
 */
import { Badge, Button, Input, Select } from '../components/ui'
import { criarAtendimento, listarAtendimentos } from '../services/api/atendimentos'
import { criarDoador } from '../services/api/doadores'
import { obterPedido } from '../services/api/pedidos'
import type { Atendimento, Pedido } from '../types/api'

export function PedidoDetalhePage() {
  const { pedidoId } = useParams()
  const numericPedidoId = Number(pedidoId)
  const [pedido, setPedido] = useState<Pedido | null>(null)
  const [atendimentos, setAtendimentos] = useState<Atendimento[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [contatoVisivel, setContatoVisivel] = useState(false)
  const [showHelpForm, setShowHelpForm] = useState(false)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)
    Promise.all([obterPedido(numericPedidoId), listarAtendimentos(numericPedidoId)])
      .then(([pedidoResponse, atendimentosResponse]) => {
        if (active) {
          setPedido(pedidoResponse)
          setAtendimentos(atendimentosResponse)
          setLoading(false)
        }
      })
      .catch(() => {
        if (active) {
          setError('Não foi possível carregar este pedido.')
          setLoading(false)
        }
      })
    return () => {
      active = false
    }
  }, [numericPedidoId])

  async function handleHelpSubmit(payload: HelpFormPayload) {
    const doador = await criarDoador({
      nome: payload.nome,
      telefone: payload.telefone,
    })
    const atendimento = await criarAtendimento(numericPedidoId, {
      doador_id: doador.id,
      tipo_ajuda: payload.tipoAjuda,
      observacao: payload.observacao,
    })
    setAtendimentos((current) => [...current, atendimento])
    setPedido((current) => (current ? { ...current, status: 'em_andamento' } : current))
    setShowHelpForm(false)
    setSuccessMessage('Ajuda registrada. Obrigado por apoiar este pedido.')
  }

  if (loading) {
    return <section className="rsp-page"><div className="rsp-skeleton">Carregando pedido...</div></section>
  }

  if (error || !pedido) {
    return <section className="rsp-page"><div className="rsp-empty">{error ?? 'Pedido não encontrado.'}</div></section>
  }

  return (
    <section className="rsp-page rsp-detail">
      <Link className="rsp-textlink" to="/pedidos">Voltar aos pedidos</Link>
      <div className="rsp-detail__layout">
        <div className="rsp-detail__main">
          <div className="rsp-detail__hero">
            <span>foto do pedido</span>
          </div>
          <div className="rsp-meta-row">
            <Badge tone={pedido.urgencia === 'alta' ? 'danger' : pedido.urgencia === 'media' ? 'warning' : 'success'}>
              {pedido.urgencia === 'alta' ? 'Urgente' : pedido.urgencia}
            </Badge>
            <Badge>{pedido.status.replace('_', ' ')}</Badge>
            <Badge>{pedido.categoria}</Badge>
          </div>
          <h1 className="rsp-detail-title">{pedido.titulo}</h1>
          <p className="rsp-prose">{pedido.descricao}</p>

          <section className="rsp-detail__section" aria-labelledby="historico-title">
            <h2 id="historico-title" className="rsp-block-label">
              Histórico de atendimentos
            </h2>
            {atendimentos.length === 0 ? (
              <p className="rsp-empty">Nenhuma ajuda registrada ainda.</p>
            ) : (
              <div className="rsp-stack">
                {atendimentos.map((atendimento) => (
                  <article className="rsp-card" key={atendimento.id}>
                    <strong>{atendimento.tipo_ajuda}</strong>
                    {atendimento.observacao && <p>{atendimento.observacao}</p>}
                  </article>
                ))}
              </div>
            )}
          </section>
        </div>

        <aside className="rsp-detail__aside">
          <div className="rsp-card rsp-detail__aside-card">
            <p className="rsp-block-label">Contato do responsável</p>
            {!contatoVisivel ? (
              <Button variant="secondary" onClick={() => setContatoVisivel(true)}>
                Mostrar contato
              </Button>
            ) : (
              <p className="rsp-contato__value">{pedido.contato}</p>
            )}
            {pedido.status !== 'concluido' && (
              <Button className="rsp-btn--block" onClick={() => setShowHelpForm((value) => !value)}>
                Quero ajudar
              </Button>
            )}
            {successMessage && <p className="rsp-success-message">{successMessage}</p>}
            {showHelpForm && <HelpForm onSubmit={handleHelpSubmit} />}
          </div>
        </aside>
      </div>
    </section>
  )
}

type HelpFormPayload = {
  nome: string
  observacao: string
  telefone: string
  tipoAjuda: string
}

type HelpFormProps = {
  onSubmit: (payload: HelpFormPayload) => Promise<void>
}

/**
 * Formulário compacto para confirmar ajuda.
 *
 * @param props - Callback de envio do formulário.
 * @returns Formulário de criação de doador e atendimento.
 */
function HelpForm({ onSubmit }: HelpFormProps) {
  const [form, setForm] = useState<HelpFormPayload>({
    nome: '',
    telefone: '',
    tipoAjuda: 'transporte',
    observacao: '',
  })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (form.nome.trim().length < 2 || form.telefone.trim().length < 5) {
      setError('Informe nome e contato para confirmar a ajuda.')
      return
    }
    setSubmitting(true)
    setError(null)
    try {
      await onSubmit({
        nome: form.nome.trim(),
        telefone: form.telefone.trim(),
        tipoAjuda: form.tipoAjuda,
        observacao: form.observacao.trim(),
      })
    } catch {
      setError('Não foi possível registrar sua ajuda. Tente novamente.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form className="rsp-help-form" onSubmit={handleSubmit}>
      {error && <p role="alert" className="rsp-alert">{error}</p>}
      <Input
        id="nome-ajuda"
        label="Seu nome"
        value={form.nome}
        onChange={(event) => setForm((current) => ({ ...current, nome: event.target.value }))}
      />
      <Input
        id="telefone-ajuda"
        label="Telefone ou WhatsApp"
        value={form.telefone}
        onChange={(event) => setForm((current) => ({ ...current, telefone: event.target.value }))}
      />
      <Select
        id="tipo-ajuda"
        label="Tipo de ajuda"
        value={form.tipoAjuda}
        onChange={(event) => setForm((current) => ({ ...current, tipoAjuda: event.target.value }))}
        options={[
          { label: 'Transporte', value: 'transporte' },
          { label: 'Ração', value: 'ração' },
          { label: 'Veterinário', value: 'veterinário' },
          { label: 'Lar temporário', value: 'lar temporário' },
        ]}
      />
      <label className="rsp-field" htmlFor="observacao-ajuda">
        <span>Observação</span>
        <textarea
          id="observacao-ajuda"
          className="rsp-input rsp-textarea"
          value={form.observacao}
          onChange={(event) => setForm((current) => ({ ...current, observacao: event.target.value }))}
        />
      </label>
      <Button type="submit" disabled={submitting}>
        {submitting ? 'Confirmando...' : 'Confirmar ajuda'}
      </Button>
    </form>
  )
}
