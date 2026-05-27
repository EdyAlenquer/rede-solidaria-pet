export type Urgencia = 'baixa' | 'media' | 'alta'

export type StatusPedido = 'aberto' | 'em_andamento' | 'concluido'

export type Pedido = {
  id: number
  titulo: string
  descricao: string
  categoria: string
  urgencia: Urgencia
  status: StatusPedido
  contato: string
  data_criacao: string
}

export type PedidoCreate = {
  titulo: string
  descricao: string
  categoria: string
  urgencia: Urgencia
  contato: string
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
  doador_id: number
  tipo_ajuda: string
  observacao?: string | null
}
