import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { Seo } from '../components/Seo'
import { obterEstatisticas } from '../services/api/estatisticas'
import type { Estatisticas } from '../types/api'

type Contador = {
  /** Rótulo PT-BR exibido sob o número. */
  rotulo: string
  /** Valor numérico do contador, ou `null` enquanto carrega/falha. */
  valor: number | null
}

/**
 * Formata um contador para exibição, usando travessão quando indisponível.
 *
 * @param valor - Número agregado ou `null` (carregando/erro).
 * @returns Texto pronto para renderizar.
 */
function formatarContador(valor: number | null): string {
  return valor === null ? '—' : valor.toLocaleString('pt-BR')
}

/**
 * Página inicial com estatísticas reais, caminhos principais e "como funciona".
 *
 * Consome `GET /estatisticas` para mostrar contadores agregados (pedidos,
 * atendimentos, cidades e animais ajudados). A copy é honesta: não promete
 * geolocalização "perto de você" que o produto não oferece.
 *
 * @returns Conteúdo de chegada com ações principais do produto.
 */
export function HomePage() {
  const [estatisticas, setEstatisticas] = useState<Estatisticas | null>(null)

  useEffect(() => {
    let active = true
    obterEstatisticas()
      .then((dados) => {
        if (active) {
          setEstatisticas(dados)
        }
      })
      .catch(() => {
        // Estatísticas são complementares: se falharem, a home segue utilizável
        // com travessões no lugar dos números.
      })
    return () => {
      active = false
    }
  }, [])

  const contadores: Contador[] = [
    { rotulo: 'Pedidos publicados', valor: estatisticas?.total_pedidos ?? null },
    { rotulo: 'Atendimentos registrados', valor: estatisticas?.total_atendimentos ?? null },
    { rotulo: 'Pedidos concluídos', valor: estatisticas?.pedidos_concluidos ?? null },
    { rotulo: 'Cidades alcançadas', valor: estatisticas?.total_cidades ?? null },
  ]

  return (
    <section className="rsp-page rsp-home">
      <Seo
        title="Início"
        description="Conectamos protetores, ONGs e voluntários para ajudar animais em situação de rua ou vulnerabilidade. Publique um pedido ou apoie a comunidade."
      />
      <div className="rsp-home__hero">
        <div>
          <p className="rsp-eyebrow">Ajuda comunitária</p>
          <h1 className="rsp-page__title">Encontre ajuda para um animal</h1>
          <p className="rsp-page__sub">
            Publique uma necessidade com clareza ou encontre pedidos abertos para apoiar
            protetores, ONGs e voluntários da rede.
          </p>
          <div className="rsp-home__actions" aria-label="Ações principais">
            <Link className="rsp-btn rsp-btn--primary" to="/pedidos">
              Ver pedidos
            </Link>
            <Link className="rsp-btn rsp-btn--secondary" to="/pedidos/novo">
              Cadastrar pedido
            </Link>
          </div>
        </div>

        <aside className="rsp-home__preview" aria-label="Exemplo de pedido">
          <div className="rsp-home__preview-top">
            <span>Pedido aberto</span>
            <strong>Urgente</strong>
          </div>
          <div className="rsp-home__preview-art">
            <img
              src="https://images.unsplash.com/photo-1548199973-03cce0bbc87b?auto=format&fit=crop&w=900&q=80"
              alt="Filhotes aguardando ajuda comunitária"
              loading="lazy"
            />
          </div>
          <h2>Ração para filhotes recém-nascidos</h2>
          <p>Protetora acolheu quatro filhotes e precisa de ração úmida ainda hoje.</p>
          <div className="rsp-home__preview-meta">
            <span>Ração</span>
            <span>Contato protegido</span>
          </div>
        </aside>
      </div>

      <div className="rsp-home__stats" aria-label="Números da rede">
        {contadores.map((contador) => (
          <article key={contador.rotulo} className="rsp-stat">
            <strong className="rsp-stat__value">{formatarContador(contador.valor)}</strong>
            <span className="rsp-stat__label">{contador.rotulo}</span>
          </article>
        ))}
      </div>

      <div className="rsp-home__guide">
        <h2 className="rsp-section-title">Como funciona</h2>
        <div className="rsp-home__guide-steps">
          <article>
            <strong>1. Conte a necessidade</strong>
            <p>
              Explique o que o animal precisa, a urgência e uma forma segura de contato.
            </p>
          </article>
          <article>
            <strong>2. A comunidade encontra</strong>
            <p>
              Voluntários filtram pedidos por categoria, status e urgência antes de agir.
            </p>
          </article>
          <article>
            <strong>3. A ajuda fica registrada</strong>
            <p>O histórico mostra quando alguém se comprometeu a apoiar o pedido.</p>
          </article>
        </div>
      </div>
    </section>
  )
}
