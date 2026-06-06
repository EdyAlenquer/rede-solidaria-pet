import { useEffect, useId, useRef, useState, type KeyboardEvent } from 'react'

import { buscarEndereco, type ResultadoEndereco } from '../utils/geocoding'

/** Intervalo (ms) de debounce entre a digitação e a busca de endereço. */
const DEBOUNCE_MS = 500

/** Tamanho mínimo do termo antes de acionar uma busca. */
const MIN_CARACTERES = 3

type CampoEnderecoProps = {
  /**
   * Chamado quando o usuário escolhe um endereço da lista, fixando o ponto
   * exato (latitude/longitude) e os dados de cidade/UF/bairro.
   */
  onSelecionar: (resultado: ResultadoEndereco) => void
}

/**
 * Campo de busca de endereço por texto (geocoding) com sugestões acessíveis.
 *
 * Implementa o padrão combobox: um input rotulado ("Endereço") e uma lista de
 * sugestões (`role="listbox"` com `option`s) navegável por teclado (setas +
 * Enter, Esc fecha). A busca é debounced (~500ms) e usa o Nominatim via
 * `buscarEndereco`. Estados de carregando e "sem resultados" aparecem em PT-BR.
 * Complementa — não substitui — o clique no mapa e a geolocalização.
 *
 * @param props - Callback `onSelecionar` chamado ao escolher uma sugestão.
 * @returns Campo de endereço com lista de sugestões.
 */
export function CampoEndereco({ onSelecionar }: CampoEnderecoProps) {
  const baseId = useId()
  const inputId = `${baseId}-endereco`
  const dicaId = `${baseId}-dica`
  const listaId = `${baseId}-lista`

  const [texto, setTexto] = useState('')
  const [resultados, setResultados] = useState<ResultadoEndereco[]>([])
  const [carregando, setCarregando] = useState(false)
  const [aberto, setAberto] = useState(false)
  const [destacado, setDestacado] = useState(-1)
  // `true` após uma busca concluída cujo retorno foi vazio (para a mensagem).
  const [buscou, setBuscou] = useState(false)

  // Quando o usuário seleciona um item, suprimimos a próxima busca disparada
  // pela mudança de texto (preenchemos o input com o label escolhido).
  const ignorarProximaBusca = useRef(false)

  useEffect(() => {
    if (ignorarProximaBusca.current) {
      ignorarProximaBusca.current = false
      return
    }

    const termo = texto.trim()
    if (termo.length < MIN_CARACTERES) {
      setResultados([])
      setAberto(false)
      setCarregando(false)
      setBuscou(false)
      return
    }

    let cancelado = false
    const temporizador = setTimeout(async () => {
      setCarregando(true)
      setAberto(true)
      const encontrados = await buscarEndereco(termo)
      if (cancelado) {
        return
      }
      setResultados(encontrados)
      setDestacado(encontrados.length > 0 ? 0 : -1)
      setCarregando(false)
      setBuscou(true)
    }, DEBOUNCE_MS)

    return () => {
      cancelado = true
      clearTimeout(temporizador)
    }
  }, [texto])

  function selecionar(resultado: ResultadoEndereco) {
    ignorarProximaBusca.current = true
    setTexto(resultado.label)
    setResultados([])
    setAberto(false)
    setDestacado(-1)
    setBuscou(false)
    onSelecionar(resultado)
  }

  function aoTeclar(evento: KeyboardEvent<HTMLInputElement>) {
    if (!aberto || resultados.length === 0) {
      return
    }
    if (evento.key === 'ArrowDown') {
      evento.preventDefault()
      setDestacado((atual) => (atual + 1) % resultados.length)
    } else if (evento.key === 'ArrowUp') {
      evento.preventDefault()
      setDestacado((atual) => (atual - 1 + resultados.length) % resultados.length)
    } else if (evento.key === 'Enter') {
      evento.preventDefault()
      const escolhido = resultados[destacado] ?? resultados[0]
      if (escolhido) {
        selecionar(escolhido)
      }
    } else if (evento.key === 'Escape') {
      setAberto(false)
    }
  }

  const mostrarVazio = aberto && buscou && !carregando && resultados.length === 0

  return (
    <div className="rsp-field-wrap rsp-campo-endereco">
      <label className="rsp-field" htmlFor={inputId}>
        <span>Endereço</span>
        <input
          id={inputId}
          type="text"
          className="rsp-input"
          value={texto}
          onChange={(evento) => setTexto(evento.target.value)}
          onKeyDown={aoTeclar}
          role="combobox"
          aria-expanded={aberto}
          aria-controls={listaId}
          aria-autocomplete="list"
          aria-describedby={dicaId}
          aria-activedescendant={
            aberto && destacado >= 0 ? `${listaId}-opcao-${destacado}` : undefined
          }
          autoComplete="off"
          placeholder="Ex.: Praça da Sé, São Paulo"
        />
      </label>
      <p id={dicaId} className="rsp-help">
        Digite e selecione para marcar no mapa.
      </p>

      {carregando && (
        <p className="rsp-help" role="status">
          Buscando endereços...
        </p>
      )}

      {mostrarVazio && (
        <p className="rsp-help" role="status">
          Nenhum endereço encontrado.
        </p>
      )}

      {aberto && resultados.length > 0 && (
        <ul id={listaId} role="listbox" className="rsp-campo-endereco__lista" aria-label="Sugestões de endereço">
          {resultados.map((resultado, indice) => (
            <li
              key={`${resultado.latitude},${resultado.longitude},${indice}`}
              id={`${listaId}-opcao-${indice}`}
              role="option"
              aria-selected={indice === destacado}
              className={`rsp-campo-endereco__opcao ${
                indice === destacado ? 'rsp-campo-endereco__opcao--ativa' : ''
              }`.trim()}
              onMouseDown={(evento) => {
                // Evita que o input perca foco antes do clique registrar.
                evento.preventDefault()
                selecionar(resultado)
              }}
              onMouseEnter={() => setDestacado(indice)}
            >
              {resultado.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default CampoEndereco
