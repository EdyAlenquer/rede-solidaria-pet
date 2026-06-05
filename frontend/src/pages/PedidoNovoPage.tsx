import { lazy, Suspense, useRef, useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { Button, Input, Select } from '../components/ui'
import { Seo } from '../components/Seo'
import { useToast } from '../components/Toast'
import { UploadImagens, type ArquivoSelecionado } from '../components/UploadImagens'
import type { Coordenada } from '../components/MapaSelecao'
import { categorias, especies, portes, sexos, ufs, urgencias } from '../constants/dominio'
import { criarPedido } from '../services/api/pedidos'
import { enviarImagem } from '../services/api/imagens'
import { isTelefoneValido, isUfValida } from '../utils/format'
import type { Especie, PedidoCreate, Porte, Sexo, Urgencia } from '../types/api'

// Import dinâmico: o Leaflet acessa `window` ao carregar e não monta bem em
// jsdom. Carregar sob demanda mantém os testes estáveis (o mapa é mockado).
const MapaSelecao = lazy(() => import('../components/MapaSelecao'))

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

type CampoErro = keyof CamposPedido | 'consentimento'

type ErrosPedido = Partial<Record<CampoErro, string>>

const estadoInicial: CamposPedido = {
  titulo: '',
  descricao: '',
  categoria: '',
  urgencia: 'media',
  contato: '',
  cidade: '',
  estado: '',
  bairro: '',
  especie: '',
  porte: '',
  sexo: '',
  idade_aproximada: '',
  quantidade: '',
}

/** Adiciona uma opção "Selecione" vazia no topo de uma lista de domínio. */
function comPlaceholder(opcoes: { value: string; label: string }[], texto = 'Selecione') {
  return [{ value: '', label: texto }, ...opcoes]
}

/**
 * Página protegida de criação de pedido com mapa, upload e consentimento.
 *
 * Valida cada campo inline (PT-BR), permite escolher a localização no mapa ou
 * via geolocalização, coleta fotos para upload e, ao enviar, cria o pedido e
 * envia as imagens em sequência antes de navegar ao detalhe.
 *
 * @returns Formulário completo de novo pedido.
 */
export function PedidoNovoPage() {
  const navigate = useNavigate()
  const { mostrar } = useToast()

  const [campos, setCampos] = useState<CamposPedido>(estadoInicial)
  const [coordenada, setCoordenada] = useState<Coordenada | null>(null)
  const [imagens, setImagens] = useState<ArquivoSelecionado[]>([])
  const [consentimento, setConsentimento] = useState(false)
  const [erros, setErros] = useState<ErrosPedido>({})
  const [erroGeral, setErroGeral] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  const tituloRef = useRef<HTMLInputElement>(null)
  const descricaoRef = useRef<HTMLTextAreaElement>(null)
  const categoriaRef = useRef<HTMLSelectElement>(null)
  const contatoRef = useRef<HTMLInputElement>(null)
  const cidadeRef = useRef<HTMLInputElement>(null)
  const estadoRef = useRef<HTMLSelectElement>(null)
  const consentimentoRef = useRef<HTMLInputElement>(null)

  function atualizar<K extends keyof CamposPedido>(campo: K, valor: string) {
    setCampos((atual) => ({ ...atual, [campo]: valor }))
    setErros((atual) => ({ ...atual, [campo]: undefined }))
  }

  function usarMinhaLocalizacao() {
    if (!navigator.geolocation) {
      mostrar('Seu navegador não permite usar a localização.', 'erro')
      return
    }
    navigator.geolocation.getCurrentPosition(
      (posicao) => {
        setCoordenada({
          latitude: posicao.coords.latitude,
          longitude: posicao.coords.longitude,
        })
      },
      () => {
        mostrar('Não foi possível obter sua localização.', 'erro')
      },
    )
  }

  function validar(): ErrosPedido {
    const proximos: ErrosPedido = {}
    if (campos.titulo.trim().length < 3) {
      proximos.titulo = 'Informe um título com pelo menos 3 caracteres.'
    }
    if (campos.descricao.trim().length < 10) {
      proximos.descricao = 'Informe uma descrição com pelo menos 10 caracteres.'
    }
    if (!campos.categoria) {
      proximos.categoria = 'Selecione uma categoria.'
    }
    if (!isTelefoneValido(campos.contato)) {
      proximos.contato = 'Informe um contato válido com DDD.'
    }
    if (campos.cidade.trim().length < 2) {
      proximos.cidade = 'Informe a cidade.'
    }
    if (!campos.estado) {
      proximos.estado = 'Selecione o estado.'
    } else if (!isUfValida(campos.estado)) {
      proximos.estado = 'Selecione um estado válido.'
    }
    if (campos.quantidade.trim() && Number(campos.quantidade) < 1) {
      proximos.quantidade = 'A quantidade deve ser pelo menos 1.'
    }
    if (!consentimento) {
      proximos.consentimento = 'É necessário aceitar a política de privacidade.'
    }
    return proximos
  }

  function focarPrimeiroInvalido(proximos: ErrosPedido) {
    const ordem: [CampoErro, { focus: () => void } | null][] = [
      ['titulo', tituloRef.current],
      ['descricao', descricaoRef.current],
      ['categoria', categoriaRef.current],
      ['contato', contatoRef.current],
      ['cidade', cidadeRef.current],
      ['estado', estadoRef.current],
      ['consentimento', consentimentoRef.current],
    ]
    for (const [campo, alvo] of ordem) {
      if (proximos[campo]) {
        alvo?.focus()
        return
      }
    }
  }

  function montarPayload(): PedidoCreate {
    const payload: PedidoCreate = {
      titulo: campos.titulo.trim(),
      descricao: campos.descricao.trim(),
      categoria: campos.categoria,
      urgencia: campos.urgencia,
      contato: campos.contato.trim(),
      cidade: campos.cidade.trim(),
      estado: campos.estado,
      consentimento_aceito: true,
    }
    if (campos.bairro.trim()) {
      payload.bairro = campos.bairro.trim()
    }
    if (coordenada) {
      payload.latitude = coordenada.latitude
      payload.longitude = coordenada.longitude
    }
    if (campos.especie) {
      payload.especie = campos.especie as Especie
    }
    if (campos.porte) {
      payload.porte = campos.porte as Porte
    }
    if (campos.sexo) {
      payload.sexo = campos.sexo as Sexo
    }
    if (campos.idade_aproximada.trim()) {
      payload.idade_aproximada = campos.idade_aproximada.trim()
    }
    if (campos.quantidade.trim()) {
      payload.quantidade = Number(campos.quantidade)
    }
    return payload
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
      const pedido = await criarPedido(montarPayload())
      // Upload das fotos em sequência após criar o pedido (precisa do id).
      for (const item of imagens) {
        await enviarImagem(pedido.id, item.arquivo)
      }
      mostrar('Pedido publicado com sucesso!', 'sucesso')
      navigate(`/pedidos/${pedido.id}`)
    } catch {
      setErroGeral('Não foi possível publicar o pedido. Tente novamente.')
    } finally {
      setEnviando(false)
    }
  }

  const restantes = DESCRICAO_MAX - campos.descricao.length

  return (
    <section className="rsp-page rsp-page--narrow rsp-formpage">
      <Seo
        title="Novo pedido"
        description="Publique um pedido de ajuda para um animal em situação de vulnerabilidade."
      />
      <div className="rsp-page__header">
        <div>
          <p className="rsp-eyebrow">Novo pedido</p>
          <h1 className="rsp-page__title">Novo pedido</h1>
          <p className="rsp-page__sub">
            Conte o que o animal precisa. As informações públicas ajudam voluntários a decidir como
            agir.
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
          ref={tituloRef}
          id="titulo"
          label="Título do pedido"
          value={campos.titulo}
          onChange={(event) => atualizar('titulo', event.target.value)}
          error={erros.titulo}
          placeholder="Ex.: Ração para filhotes recém-nascidos"
        />

        <div className="rsp-field-wrap">
          <label className="rsp-field" htmlFor="descricao">
            <span>Descrição</span>
            <textarea
              ref={descricaoRef}
              id="descricao"
              className={`rsp-input rsp-textarea ${erros.descricao ? 'rsp-input--erro' : ''}`.trim()}
              value={campos.descricao}
              maxLength={DESCRICAO_MAX}
              aria-invalid={erros.descricao ? true : undefined}
              aria-describedby={erros.descricao ? 'descricao-erro' : 'descricao-contador'}
              onChange={(event) => atualizar('descricao', event.target.value)}
              placeholder="Explique a situação, o que precisa e como ajudar."
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
            ref={categoriaRef}
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
          ref={contatoRef}
          id="contato"
          label="Contato"
          value={campos.contato}
          onChange={(event) => atualizar('contato', event.target.value)}
          error={erros.contato}
          placeholder="WhatsApp ou telefone com DDD"
        />
        <p className="rsp-help">
          O contato fica protegido na tela de detalhe até um clique explícito.
        </p>

        <div className="rsp-form-grid">
          <Input
            ref={cidadeRef}
            id="cidade"
            label="Cidade"
            value={campos.cidade}
            onChange={(event) => atualizar('cidade', event.target.value)}
            error={erros.cidade}
            placeholder="Ex.: São Paulo"
          />
          <Select
            ref={estadoRef}
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
          placeholder="Ex.: Vila Esperança"
        />

        <fieldset className="rsp-fieldset">
          <legend className="rsp-block-label">Localização no mapa (opcional)</legend>
          <p className="rsp-help">
            Clique no mapa para marcar o ponto ou use sua localização atual. Ajuda voluntários a se
            orientarem sem expor um endereço exato.
          </p>
          <Button variant="secondary" onClick={usarMinhaLocalizacao}>
            Usar minha localização
          </Button>
          <Suspense fallback={<div className="rsp-skeleton">Carregando mapa...</div>}>
            <MapaSelecao valor={coordenada} onSelecionar={setCoordenada} />
          </Suspense>
          {coordenada && (
            <p className="rsp-help">
              Ponto selecionado: {coordenada.latitude.toFixed(5)}, {coordenada.longitude.toFixed(5)}
            </p>
          )}
        </fieldset>

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
              placeholder="Ex.: 2 meses"
            />
            <Input
              id="quantidade"
              type="number"
              min={1}
              label="Quantidade de animais"
              value={campos.quantidade}
              onChange={(event) => atualizar('quantidade', event.target.value)}
              error={erros.quantidade}
              placeholder="Ex.: 1"
            />
          </div>
        </fieldset>

        <UploadImagens
          id="fotos"
          label="Fotos (opcional)"
          arquivos={imagens}
          onChange={setImagens}
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
              Aceito a <Link to="/privacidade">política de privacidade</Link> e autorizo a
              publicação destas informações para fins de ajuda ao animal.
            </span>
          </label>
          {erros.consentimento && (
            <span id="consentimento-erro" className="rsp-field__erro" role="alert">
              {erros.consentimento}
            </span>
          )}
        </div>

        <Button type="submit" disabled={enviando}>
          {enviando ? 'Publicando...' : 'Publicar pedido'}
        </Button>
      </form>
    </section>
  )
}
