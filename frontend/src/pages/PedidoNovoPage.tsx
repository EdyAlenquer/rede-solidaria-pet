import type { FormEvent } from 'react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { Button, Input, Select } from '../components/ui'
import { criarPedido } from '../services/api/pedidos'
import type { PedidoCreate, Urgencia } from '../types/api'

type FormState = PedidoCreate

const initialForm: FormState = {
  titulo: '',
  descricao: '',
  categoria: '',
  urgencia: 'media',
  contato: '',
}

/**
 * Página de cadastro de pedido com validação client-side.
 *
 * @returns Formulário de novo pedido integrado à API.
 */
export function PedidoNovoPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState<FormState>(initialForm)
  const [errors, setErrors] = useState<string[]>([])
  const [submitting, setSubmitting] = useState(false)

  function updateField<K extends keyof FormState>(field: K, value: FormState[K]) {
    setForm((current) => ({ ...current, [field]: value }))
  }

  function validate() {
    const nextErrors: string[] = []
    if (form.titulo.trim().length < 3) {
      nextErrors.push('Informe um título com pelo menos 3 caracteres.')
    }
    if (!form.categoria.trim()) {
      nextErrors.push('Informe uma categoria.')
    }
    if (form.descricao.trim().length < 10) {
      nextErrors.push('Informe uma descrição com pelo menos 10 caracteres.')
    }
    if (form.contato.trim().length < 5) {
      nextErrors.push('Informe um contato para retorno.')
    }
    return nextErrors
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const nextErrors = validate()
    setErrors(nextErrors)
    if (nextErrors.length > 0) {
      return
    }
    setSubmitting(true)
    try {
      const pedido = await criarPedido({
        titulo: form.titulo.trim(),
        categoria: form.categoria.trim(),
        urgencia: form.urgencia,
        descricao: form.descricao.trim(),
        contato: form.contato.trim(),
      })
      navigate(`/pedidos/${pedido.id}`)
    } catch {
      setErrors(['Não foi possível publicar o pedido. Tente novamente.'])
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="rsp-page rsp-page--narrow rsp-formpage">
      <div className="rsp-page__header">
        <div>
          <p className="rsp-eyebrow">Novo pedido</p>
          <h1 className="rsp-page__title">Novo pedido</h1>
          <p className="rsp-page__sub">
            Conte o que o animal precisa. As informações públicas ajudam voluntários a decidir como agir.
          </p>
        </div>
      </div>

      <form className="rsp-card rsp-form" onSubmit={handleSubmit} noValidate>
        {errors.length > 0 && (
          <div className="rsp-alert" role="alert">
            {errors.map((error) => (
              <p key={error}>{error}</p>
            ))}
          </div>
        )}
        <Input
          id="titulo"
          label="Título do pedido"
          value={form.titulo}
          onChange={(event) => updateField('titulo', event.target.value)}
          placeholder="Ex: Ração para filhotes recém-nascidos"
        />
        <Select
          id="categoria"
          label="Categoria"
          value={form.categoria}
          onChange={(event) => updateField('categoria', event.target.value)}
          options={[
            { label: 'Selecione', value: '' },
            { label: 'Ração', value: 'ração' },
            { label: 'Transporte', value: 'transporte' },
            { label: 'Veterinário', value: 'veterinário' },
            { label: 'Lar temporário', value: 'lar temporário' },
          ]}
        />
        <Select
          id="urgencia"
          label="Urgência"
          value={form.urgencia}
          onChange={(event) => updateField('urgencia', event.target.value as Urgencia)}
          options={[
            { label: 'Alta', value: 'alta' },
            { label: 'Média', value: 'media' },
            { label: 'Baixa', value: 'baixa' },
          ]}
        />
        <label className="rsp-field" htmlFor="descricao">
          <span>Descrição</span>
          <textarea
            id="descricao"
            className="rsp-input rsp-textarea"
            value={form.descricao}
            onChange={(event) => updateField('descricao', event.target.value)}
            placeholder="Explique a situação, o que precisa e como ajudar."
            rows={6}
          />
        </label>
        <Input
          id="contato"
          label="Contato"
          value={form.contato}
          onChange={(event) => updateField('contato', event.target.value)}
          placeholder="WhatsApp, telefone ou e-mail"
        />
        <p className="rsp-help">
          O contato fica protegido na tela de detalhe até um clique explícito.
        </p>
        <Button type="submit" disabled={submitting}>
          {submitting ? 'Publicando...' : 'Publicar pedido'}
        </Button>
      </form>
    </section>
  )
}
