/**
 * Geocodificação de endereços via Nominatim/OpenStreetMap.
 *
 * Converte um texto livre (ex.: "Praça da Sé, São Paulo") em coordenadas e
 * dados de endereço, para que o usuário fixe o ponto exato no mapa sem depender
 * apenas do clique. Usa `fetch` nativo (sem dependências novas) e degrada com
 * segurança: qualquer falha de rede ou resposta inesperada retorna `[]`, de
 * modo que o clique no mapa continua sendo um caminho válido.
 */

/** Endereço resolvido a partir de uma busca textual. */
export type ResultadoEndereco = {
  /** Texto descritivo completo do endereço (Nominatim `display_name`). */
  label: string
  /** Latitude em graus decimais. */
  latitude: number
  /** Longitude em graus decimais. */
  longitude: number
  /** Município, quando disponível. */
  cidade?: string
  /** Sigla da UF (2 letras), quando o estado pôde ser mapeado. */
  estado?: string
  /** Bairro, quando disponível. */
  bairro?: string
}

/** Endereço estruturado retornado pelo Nominatim (`addressdetails=1`). */
type EnderecoNominatim = {
  city?: string
  town?: string
  village?: string
  municipality?: string
  state?: string
  suburb?: string
  neighbourhood?: string
}

/** Item bruto da resposta do Nominatim no formato `jsonv2`. */
type ItemNominatim = {
  display_name?: string
  lat?: string
  lon?: string
  address?: EnderecoNominatim
}

const URL_BASE = 'https://nominatim.openstreetmap.org/search'

/** Nome do estado (sem distinção de caixa) para a sigla de UF correspondente. */
const NOME_PARA_UF: Record<string, string> = {
  acre: 'AC',
  alagoas: 'AL',
  amapá: 'AP',
  amazonas: 'AM',
  bahia: 'BA',
  ceará: 'CE',
  'distrito federal': 'DF',
  'espírito santo': 'ES',
  goiás: 'GO',
  maranhão: 'MA',
  'mato grosso': 'MT',
  'mato grosso do sul': 'MS',
  'minas gerais': 'MG',
  pará: 'PA',
  paraíba: 'PB',
  paraná: 'PR',
  pernambuco: 'PE',
  piauí: 'PI',
  'rio de janeiro': 'RJ',
  'rio grande do norte': 'RN',
  'rio grande do sul': 'RS',
  rondônia: 'RO',
  roraima: 'RR',
  'santa catarina': 'SC',
  'são paulo': 'SP',
  sergipe: 'SE',
  tocantins: 'TO',
}

/**
 * Converte o nome de um estado brasileiro na sigla de UF (2 letras).
 *
 * @param nome - Nome do estado (ex.: "São Paulo"); pode ser indefinido.
 * @returns Sigla da UF (ex.: "SP"), ou `undefined` quando não reconhecido.
 */
function nomeEstadoParaUf(nome: string | undefined): string | undefined {
  if (!nome) {
    return undefined
  }
  return NOME_PARA_UF[nome.trim().toLowerCase()]
}

/**
 * Deriva um `ResultadoEndereco` a partir de um item bruto do Nominatim.
 *
 * @param item - Item retornado pela API; campos podem faltar.
 * @returns Endereço normalizado, ou `null` quando faltam dados essenciais
 *   (label/lat/lon inválidos).
 */
function mapearItem(item: ItemNominatim): ResultadoEndereco | null {
  const latitude = Number(item.lat)
  const longitude = Number(item.lon)
  if (!item.display_name || Number.isNaN(latitude) || Number.isNaN(longitude)) {
    return null
  }

  const endereco = item.address ?? {}
  const cidade = endereco.city ?? endereco.town ?? endereco.village ?? endereco.municipality
  const estado = nomeEstadoParaUf(endereco.state)
  const bairro = endereco.suburb ?? endereco.neighbourhood

  const resultado: ResultadoEndereco = {
    label: item.display_name,
    latitude,
    longitude,
  }
  if (cidade) {
    resultado.cidade = cidade
  }
  if (estado) {
    resultado.estado = estado
  }
  if (bairro) {
    resultado.bairro = bairro
  }
  return resultado
}

/**
 * Busca endereços que correspondam a um texto livre, no Brasil, em PT-BR.
 *
 * Consulta o Nominatim/OpenStreetMap e normaliza cada resultado (coordenadas,
 * cidade, UF e bairro). É tolerante a falhas: consulta vazia, erro de rede ou
 * resposta inválida resultam em `[]`, preservando o clique no mapa como
 * alternativa para o usuário.
 *
 * @param query - Texto do endereço a procurar (ex.: "Rua das Flores, Curitiba").
 * @returns Lista de até 5 endereços resolvidos; `[]` quando nada é encontrado
 *   ou em caso de erro.
 */
export async function buscarEndereco(query: string): Promise<ResultadoEndereco[]> {
  const termo = query.trim()
  if (!termo) {
    return []
  }

  const params = new URLSearchParams({
    format: 'jsonv2',
    addressdetails: '1',
    countrycodes: 'br',
    'accept-language': 'pt-BR',
    limit: '5',
    q: termo,
  })

  try {
    const resposta = await fetch(`${URL_BASE}?${params.toString()}`)
    if (!resposta.ok) {
      return []
    }
    const dados = (await resposta.json()) as ItemNominatim[]
    if (!Array.isArray(dados)) {
      return []
    }
    return dados
      .map(mapearItem)
      .filter((item): item is ResultadoEndereco => item !== null)
  } catch {
    // Falha de rede/parse: o usuário ainda pode clicar no mapa para marcar.
    return []
  }
}
