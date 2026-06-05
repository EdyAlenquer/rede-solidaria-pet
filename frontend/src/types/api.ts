export type Urgencia = 'baixa' | 'media' | 'alta'

export type StatusPedido = 'aberto' | 'em_andamento' | 'concluido' | 'cancelado'

export type Especie = 'cao' | 'gato' | 'outro'

export type Porte = 'pequeno' | 'medio' | 'grande'

export type Sexo = 'macho' | 'femea' | 'desconhecido'

export type Papel = 'protetor' | 'admin'

export type MotivoDenuncia = 'spam' | 'golpe' | 'conteudo_improprio' | 'outro'

export type ImagemRead = {
  id: number
  url: string
  ordem: number
}

export type Pedido = {
  id: number
  titulo: string
  descricao: string
  categoria: string
  urgencia: Urgencia
  status: StatusPedido
  data_criacao: string
  cidade?: string
  estado?: string
  bairro?: string | null
  latitude?: number | null
  longitude?: number | null
  especie?: Especie | null
  porte?: Porte | null
  sexo?: Sexo | null
  idade_aproximada?: string | null
  quantidade?: number
  imagens?: ImagemRead[]
  /** Total de atendimentos, quando o backend o inclui no payload. */
  total_atendimentos?: number
  /** Id do autor, quando o backend o inclui (usado para ações de gestão). */
  autor_id?: number | null
}

/**
 * Pedido com o `contato` próprio, retornado apenas em rotas privadas do titular
 * (ex.: exportação LGPD `GET /me/dados`). A leitura pública (`Pedido`) nunca
 * traz o contato — ele só é revelado via `GET /pedidos/{id}/contato`.
 */
export type PedidoMeu = Pedido & {
  contato: string
}

export type PedidoCreate = {
  titulo: string
  descricao: string
  categoria: string
  urgencia: Urgencia
  contato: string
  cidade: string
  estado: string
  bairro?: string | null
  latitude?: number | null
  longitude?: number | null
  especie?: Especie | null
  porte?: Porte | null
  sexo?: Sexo | null
  idade_aproximada?: string | null
  quantidade?: number
  consentimento_aceito: true
}

export type PedidoUpdate = Partial<
  Omit<PedidoCreate, 'consentimento_aceito'>
>

export type PedidoContato = {
  contato: string
  whatsapp?: string | null
}

export type PageInfo = {
  page: number
  page_size: number
  total: number
  total_pages: number
}

export type PedidoPage = {
  items: Pedido[]
  page_info: PageInfo
}

export type Doador = {
  id: number
  nome: string
  telefone: string | null
  email: string | null
}

export type DoadorCreate = {
  nome: string
  telefone?: string | null
  email?: string | null
}

export type Atendimento = {
  id: number
  pedido_id: number
  tipo_ajuda: string
  observacao: string | null
  data_contato: string
}

export type AtendimentoCreate = {
  tipo_ajuda: string
  observacao?: string | null
}

export type UsuarioRead = {
  id: number
  nome: string
  email: string
  papel: Papel
}

/** Alias semântico para o usuário autenticado retornado pela API. */
export type Usuario = UsuarioRead

export type RegistroPayload = {
  nome: string
  email: string
  senha: string
  telefone?: string | null
  consentimento_aceito: true
}

export type LoginPayload = {
  email: string
  senha: string
}

export type TokenResponse = {
  access_token: string
  token_type: string
}

export type Estatisticas = {
  total_pedidos: number
  pedidos_abertos: number
  pedidos_concluidos: number
  total_atendimentos: number
  total_cidades: number
}

export type DenunciaCreate = {
  motivo: MotivoDenuncia
  descricao?: string | null
}

export type MeusDados = {
  perfil: UsuarioRead
  pedidos: PedidoMeu[]
  atendimentos: Atendimento[]
}
