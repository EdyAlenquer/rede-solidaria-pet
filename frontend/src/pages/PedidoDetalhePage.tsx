import { useParams } from 'react-router-dom'

/**
 * Página placeholder para detalhe de pedido.
 *
 * @returns Estrutura inicial da rota de detalhe.
 */
export function PedidoDetalhePage() {
  const { pedidoId } = useParams()

  return (
    <section className="rsp-page rsp-page--narrow">
      <div className="rsp-page__header">
        <div>
          <h1 className="rsp-page__title">Detalhe do pedido</h1>
          <p className="rsp-page__sub">
            Pedido #{pedidoId} receberá contato, status e histórico de atendimentos na Fase 6.
          </p>
        </div>
      </div>
    </section>
  )
}
