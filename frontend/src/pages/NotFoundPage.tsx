import { Link } from 'react-router-dom'

import { Seo } from '../components/Seo'

/**
 * Página 404 amigável com retorno para a página inicial.
 *
 * @returns Conteúdo de rota não encontrada.
 */
export function NotFoundPage() {
  return (
    <section className="rsp-page rsp-notfound">
      <Seo title="Página não encontrada" />
      <p className="rsp-eyebrow">Erro 404</p>
      <h1 className="rsp-page__title">Página não encontrada</h1>
      <p className="rsp-page__sub">
        O endereço que você tentou abrir não existe ou foi movido.
      </p>
      <Link className="rsp-btn rsp-btn--primary" to="/">
        Voltar para o início
      </Link>
    </section>
  )
}
