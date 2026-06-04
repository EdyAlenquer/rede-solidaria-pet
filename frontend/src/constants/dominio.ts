/**
 * Constantes de domínio compartilhadas (value/label PT-BR).
 *
 * O `value` (sem acento) é o contrato enviado/recebido da API; o `label` é
 * sempre o texto PT-BR exibido ao usuário. Centralizar aqui evita listas
 * divergentes espalhadas pelas páginas.
 */

export type OpcaoDominio = {
  value: string
  label: string
}

/** Categorias de ajuda de um pedido. */
export const categorias: OpcaoDominio[] = [
  { value: 'racao', label: 'Ração' },
  { value: 'transporte', label: 'Transporte' },
  { value: 'veterinario', label: 'Veterinário' },
  { value: 'lar_temporario', label: 'Lar temporário' },
  { value: 'resgate', label: 'Resgate' },
]

/** Níveis de urgência. */
export const urgencias: OpcaoDominio[] = [
  { value: 'baixa', label: 'Baixa' },
  { value: 'media', label: 'Média' },
  { value: 'alta', label: 'Urgente' },
]

/** Estados do ciclo de vida de um pedido. */
export const status: OpcaoDominio[] = [
  { value: 'aberto', label: 'Aberto' },
  { value: 'em_andamento', label: 'Em andamento' },
  { value: 'concluido', label: 'Concluído' },
  { value: 'cancelado', label: 'Cancelado' },
]

/** Espécies do animal. */
export const especies: OpcaoDominio[] = [
  { value: 'cao', label: 'Cão' },
  { value: 'gato', label: 'Gato' },
  { value: 'outro', label: 'Outro' },
]

/** Portes físicos aproximados. */
export const portes: OpcaoDominio[] = [
  { value: 'pequeno', label: 'Pequeno' },
  { value: 'medio', label: 'Médio' },
  { value: 'grande', label: 'Grande' },
]

/** Sexo do animal. */
export const sexos: OpcaoDominio[] = [
  { value: 'macho', label: 'Macho' },
  { value: 'femea', label: 'Fêmea' },
  { value: 'desconhecido', label: 'Desconhecido' },
]

/** Motivos disponíveis ao denunciar um pedido. */
export const motivosDenuncia: OpcaoDominio[] = [
  { value: 'spam', label: 'Spam' },
  { value: 'golpe', label: 'Golpe' },
  { value: 'conteudo_improprio', label: 'Conteúdo impróprio' },
  { value: 'outro', label: 'Outro' },
]

/** Unidades federativas do Brasil (sigla + nome). */
export const ufs: OpcaoDominio[] = [
  { value: 'AC', label: 'Acre' },
  { value: 'AL', label: 'Alagoas' },
  { value: 'AP', label: 'Amapá' },
  { value: 'AM', label: 'Amazonas' },
  { value: 'BA', label: 'Bahia' },
  { value: 'CE', label: 'Ceará' },
  { value: 'DF', label: 'Distrito Federal' },
  { value: 'ES', label: 'Espírito Santo' },
  { value: 'GO', label: 'Goiás' },
  { value: 'MA', label: 'Maranhão' },
  { value: 'MT', label: 'Mato Grosso' },
  { value: 'MS', label: 'Mato Grosso do Sul' },
  { value: 'MG', label: 'Minas Gerais' },
  { value: 'PA', label: 'Pará' },
  { value: 'PB', label: 'Paraíba' },
  { value: 'PR', label: 'Paraná' },
  { value: 'PE', label: 'Pernambuco' },
  { value: 'PI', label: 'Piauí' },
  { value: 'RJ', label: 'Rio de Janeiro' },
  { value: 'RN', label: 'Rio Grande do Norte' },
  { value: 'RS', label: 'Rio Grande do Sul' },
  { value: 'RO', label: 'Rondônia' },
  { value: 'RR', label: 'Roraima' },
  { value: 'SC', label: 'Santa Catarina' },
  { value: 'SP', label: 'São Paulo' },
  { value: 'SE', label: 'Sergipe' },
  { value: 'TO', label: 'Tocantins' },
]

/** Conjunto de siglas de UF válidas, para validação rápida. */
export const ufsValidas: ReadonlySet<string> = new Set(ufs.map((uf) => uf.value))

/**
 * Resolve o label PT-BR de um value dentro de uma lista de domínio.
 *
 * @param opcoes - Lista de opções de domínio.
 * @param value - Value buscado (contrato da API).
 * @returns Label correspondente, ou o próprio value quando não encontrado.
 */
export function rotuloDe(opcoes: OpcaoDominio[], value: string | null | undefined): string {
  if (!value) {
    return ''
  }
  return opcoes.find((opcao) => opcao.value === value)?.label ?? value
}
