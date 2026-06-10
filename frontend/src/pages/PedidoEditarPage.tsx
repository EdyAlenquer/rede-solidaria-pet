import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'
import { Button, Input, Select } from '../components/ui'
import { Seo } from '../components/Seo'
import { useToast } from '../components/Toast'
import { categorias, especies, portes, sexos, ufs, urgencias } from '../constants/dominio'
import { editarPedido, obterPedido } from '../services/api/pedidos'
import { isTelefoneValido, isUfValida } from '../utils/format'
import type {
  Especie,
  Pedido,
  PedidoUpdate,
  Porte,
  Sexo,
  Urgencia,
} from '../types/api'

const DESCRICAO_MAX = 1000

type CamposPedido = {
  titulo: string
  descricao: string
  categoria: string
  urgencia: Urgencia
  contato: string
  cidade: string
  estado: string
  bairro: string
  especie: string
  porte: string
  sexo: string
  idade_aproximada: string
  quantidade: string
}

type ErrosPedido = Partial<Record<keyof CamposPedido, string>>

/** Adiciona uma opção "Selecione" vazia no topo de uma lista de domínio. */
function comPlaceholder(opcoes: { value: string; label: string }[], texto = 'Selecione') {
  return [{ value: '', label: texto }, ...opcoes]
}

/** Converte o pedido carregado nos campos controlados do formulário. */
function pedidoParaCampos(pedido: Pedido): CamposPedido {
  return {
    titulo: pedido.titulo,
    descricao: pedido.descricao,
    categoria: pedido.categoria,
    urgencia: pedido.urgencia,
    // O contato nunca volta na leitura pública; fica em branco até ser reescrito.
    contato: '',
    cidade: pedido.cidade ?? '',
    estado: pedido.estado ?? '',
    bairro: pedido.bairro ?? '',
    especie: pedido.especie ?? '',
    porte: pedido.porte ?? '',
    sexo: pedido.sexo ?? '',
    idade_aproximada: pedido.idade_aproximada ?? '',
    quantidade: pedido.quantidade != null ? String(pedido.quantidade) : '',
  }
}

/**
 * Página protegida de edição de pedido (`/pedidos/:pedidoId/editar`).
 *
 * Carrega o pedido, popula o formulário (reusando os campos de criação) e faz
 * `PATCH /pedidos/{id}`. Mostra mensagens amigáveis em 403/404 e valida os
 * campos editados antes de enviar. O backend é a fonte de verdade da
 * autorização (autor/admin).
 *
 * @returns Formulário de edição do pedido.
 */
export function PedidoEditarPage() {
  const { pedidoId } = useParams()
  const numericPedidoId = Number(pedidoId)
  const pedidoIdValido = Number.isInteger(numericPedidoId) && numericPedidoId > 0
  const navigate = useNavigate()
  const { mostrar } = useToast()
  const { usuario } = useAuth()

  const [campos, setCampos] = useState<CamposPedido | null>(null)
  const [erros, setErros] = useState<ErrosPedido>({})
  const [erroGeral, setErroGeral] = useState<string | null>(null)
  const [carregando, setCarregando] = useState(true)
  const [erroCarregar, setErroCarregar] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  useEffect(() => {
    let ativo = true
    if (!pedidoIdValido) {
      setCampos(null)
      setErroCarregar('Pedido não encontrado.')
      setCarregando(false)
      return () => {
        ativo = false
      }
    }
    setCarregando(true)
    setErroCarregar(null)
    obterPedido(numericPedidoId)
      .then((pedido) => {
        if (!ativo) {
          return
        }
        // Só o autor (ou admin) pode editar; sem o autor_id no payload público,
        // a checagem definitiva é do backend, mas evitamos abrir a edição quando
        // sabemos que o usuário não é o autor.
        if (pedido.autor_id != null && usuario && pedido.autor_id !== usuario.id && usuario.papel !== 'admin') {
          setErroCarregar('Você não tem permissão para editar este pedido.')
          setCarregando(false)
          return
        }
        setCampos(pedidoParaCampos(pedido))
        setCarregando(false)
      })
      .catch((erro: { response?: { status?: number } }) => {
        if (!ativo) {
          return
        }
        const status = erro?.response?.status
        if (status === 403) {
          setErroCarregar('Você não tem permissão para editar este pedido.')
        } else if (status === 404) {
          setErroCarregar('Pedido não encontrado.')
        } else {
          setErroCarregar('Não foi possível carregar este pedido.')
        }
        setCarregando(false)
      })
    return () => {
      ativo = false
    }
  }, [numericPedidoId, pedidoIdValido, usuario])

  function atualizar<K extends keyof CamposPedido>(campo: K, valor: string) {
    setCampos((atual) => (atual ? { ...atual, [campo]: valor } : atual))
    setErros((atual) => ({ ...atual, [campo]: undefined }))
  }

  function validar(atual: CamposPedido): ErrosPedido {
    const proximos: ErrosPedido = {}
    if (atual.titulo.trim().length < 3) {
      proximos.titulo = 'Informe um título com pelo menos 3 caracteres.'
    }
    if (atual.descricao.trim().length < 10) {
      proximos.descricao = 'Informe uma descrição com pelo menos 10 caracteres.'
    }
    if (!atual.categoria) {
      proximos.categoria = 'Selecione uma categoria.'
    }
    if (atual.contato.trim() && !isTelefoneValido(atual.contato)) {
      proximos.contato = 'Informe um contato válido com DDD.'
    }
    if (atual.cidade.trim().length < 2) {
      proximos.cidade = 'Informe a cidade.'
    }
    if (!atual.estado) {
      proximos.estado = 'Selecione o estado.'
    } else if (!isUfValida(atual.estado)) {
      proximos.estado = 'Selecione um estado válido.'
    }
    if (atual.quantidade.trim() && Number(atual.quantidade) < 1) {
      proximos.quantidade = 'A quantidade deve ser pelo menos 1.'
    }
    return proximos
  }

  function montarPayload(atual: CamposPedido): PedidoUpdate {
    const payload: PedidoUpdate = {
      titulo: atual.titulo.trim(),
      descricao: atual.descricao.trim(),
      categoria: atual.categoria,
      urgencia: atual.urgencia,
      cidade: atual.cidade.trim(),
      estado: atual.estado,
      bairro: atual.bairro.trim() || null,
      especie: (atual.especie || null) as Especie | null,
      porte: (atual.porte || null) as Porte | null,
      sexo: (atual.sexo || null) as Sexo | null,
      idade_aproximada: atual.idade_aproximada.trim() || null,
    }
    // O contato só é enviado quando reescrito (a leitura pública não o traz).
    if (atual.contato.trim()) {
      payload.contato = atual.contato.trim()
    }
    if (atual.quantidade.trim()) {
      payload.quantidade = Number(atual.quantidade)
    }
    return payload
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!campos) {
      return
    }
    setErroGeral(null)
    const proximos = validar(campos)
    setErros(proximos)
    if (Object.keys(proximos).length > 0) {
      return
    }
    setEnviando(true)
    try {
      await editarPedido(numericPedidoId, montarPayload(campos))
      mostrar('Pedido atualizado com sucesso!', 'sucesso')
      navigate(`/pedidos/${numericPedidoId}`)
    } catch (erro) {
      const status = (erro as { response?: { status?: number } })?.response?.status
      if (status === 403) {
        setErroGeral('Você não tem permissão para editar este pedido.')
      } else if (status === 404) {
        setErroGeral('Pedido não encontrado.')
      } else {
        setErroGeral('Não foi possível salvar as alterações. Tente novamente.')
      }
    } finally {
      setEnviando(false)
    }
  }

  if (carregando) {
    return (
      <section className="rsp-page">
        <div className="rsp-skeleton" role="status">
          Carregando pedido...
        </div>
      </section>
    )
  }

  if (erroCarregar || !campos) {
    return (
      <section className="rsp-page">
        <div className="rsp-empty">
          <p>{erroCarregar ?? 'Pedido não encontrado.'}</p>
          <Link className="rsp-textlink" to="/pedidos">
            Voltar aos pedidos
          </Link>
        </div>
      </section>
    )
  }

  const restantes = DESCRICAO_MAX - campos.descricao.length

  return (
    <section className="rsp-page rsp-page--narrow rsp-formpage">
      <Seo title="Editar pedido" description="Atualize as informações de um pedido de ajuda." />
      <div className="rsp-page__header">
        <div>
          <p className="rsp-eyebrow">Editar pedido</p>
          <h1 className="rsp-page__title">Editar pedido</h1>
          <p className="rsp-page__sub">Atualize as informações públicas deste pedido.</p>
        </div>
        <Link className="rsp-textlink" to={`/pedidos/${numericPedidoId}`}>
          Voltar ao pedido
        </Link>
      </div>

      <form className="rsp-card rsp-form" onSubmit={handleSubmit} noValidate>
        {erroGeral && (
          <div className="rsp-alert" role="alert">
            <p>{erroGeral}</p>
          </div>
        )}

        <Input
          id="titulo"
          label="Título do pedido"
          value={campos.titulo}
          onChange={(event) => atualizar('titulo', event.target.value)}
          error={erros.titulo}
        />

        <div className="rsp-field-wrap">
          <label className="rsp-field" htmlFor="descricao">
            <span>Descrição</span>
            <textarea
              id="descricao"
              className={`rsp-input rsp-textarea ${erros.descricao ? 'rsp-input--erro' : ''}`.trim()}
              value={campos.descricao}
              maxLength={DESCRICAO_MAX}
              aria-invalid={erros.descricao ? true : undefined}
              aria-describedby={erros.descricao ? 'descricao-erro' : 'descricao-contador'}
              onChange={(event) => atualizar('descricao', event.target.value)}
              rows={6}
            />
          </label>
          <p id="descricao-contador" className="rsp-help rsp-contador">
            {restantes} caracteres restantes
          </p>
          {erros.descricao && (
            <span id="descricao-erro" className="rsp-field__erro" role="alert">
              {erros.descricao}
            </span>
          )}
        </div>

        <div className="rsp-form-grid">
          <Select
            id="categoria"
            label="Categoria"
            value={campos.categoria}
            onChange={(event) => atualizar('categoria', event.target.value)}
            error={erros.categoria}
            options={comPlaceholder(categorias)}
          />
          <Select
            id="urgencia"
            label="Urgência"
            value={campos.urgencia}
            onChange={(event) => atualizar('urgencia', event.target.value as Urgencia)}
            options={urgencias}
          />
        </div>

        <Input
          id="contato"
          label="Contato"
          value={campos.contato}
          onChange={(event) => atualizar('contato', event.target.value)}
          error={erros.contato}
          placeholder="Deixe em branco para manter o contato atual"
        />
        <p className="rsp-help">
          Por privacidade, o contato atual não é exibido. Preencha apenas se quiser substituí-lo.
        </p>

        <div className="rsp-form-grid">
          <Input
            id="cidade"
            label="Cidade"
            value={campos.cidade}
            onChange={(event) => atualizar('cidade', event.target.value)}
            error={erros.cidade}
          />
          <Select
            id="estado"
            label="Estado"
            value={campos.estado}
            onChange={(event) => atualizar('estado', event.target.value)}
            error={erros.estado}
            options={comPlaceholder(ufs, 'UF')}
          />
        </div>

        <Input
          id="bairro"
          label="Bairro (opcional)"
          value={campos.bairro}
          onChange={(event) => atualizar('bairro', event.target.value)}
        />

        <fieldset className="rsp-fieldset">
          <legend className="rsp-block-label">Sobre o animal (opcional)</legend>
          <div className="rsp-form-grid">
            <Select
              id="especie"
              label="Espécie"
              value={campos.especie}
              onChange={(event) => atualizar('especie', event.target.value)}
              options={comPlaceholder(especies, 'Não informado')}
            />
            <Select
              id="porte"
              label="Porte"
              value={campos.porte}
              onChange={(event) => atualizar('porte', event.target.value)}
              options={comPlaceholder(portes, 'Não informado')}
            />
            <Select
              id="sexo"
              label="Sexo"
              value={campos.sexo}
              onChange={(event) => atualizar('sexo', event.target.value)}
              options={comPlaceholder(sexos, 'Não informado')}
            />
            <Input
              id="idade_aproximada"
              label="Idade aproximada"
              value={campos.idade_aproximada}
              onChange={(event) => atualizar('idade_aproximada', event.target.value)}
            />
            <Input
              id="quantidade"
              type="number"
              min={1}
              label="Quantidade de animais"
              value={campos.quantidade}
              onChange={(event) => atualizar('quantidade', event.target.value)}
              error={erros.quantidade}
            />
          </div>
        </fieldset>

        <div className="rsp-form-actions">
          <Link className="rsp-btn rsp-btn--secondary" to={`/pedidos/${numericPedidoId}`}>
            Cancelar
          </Link>
          <Button type="submit" disabled={enviando}>
            {enviando ? 'Salvando...' : 'Salvar alterações'}
          </Button>
        </div>
      </form>
    </section>
  )
}
