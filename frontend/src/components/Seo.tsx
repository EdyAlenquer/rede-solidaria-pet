import { Helmet } from 'react-helmet-async'

const NOME_SITE = 'Rede Solidária Pet'
const DESCRICAO_PADRAO =
  'Conectamos protetores, ONGs e voluntários para ajudar animais em situação de rua ou vulnerabilidade.'
const IMAGEM_PADRAO = '/favicon.svg'

type SeoProps = {
  /** Título da página (compõe "Título · Rede Solidária Pet"). */
  title?: string
  /** Descrição para mecanismos de busca e cartões sociais. */
  description?: string
  /** URL de imagem para OpenGraph/Twitter. */
  image?: string
}

/**
 * Define metadados de SEO e social da página atual via react-helmet-async.
 *
 * @param props - Título, descrição e imagem opcionais.
 * @returns Tags de `<head>` gerenciadas pelo Helmet.
 */
export function Seo({ title, description = DESCRICAO_PADRAO, image = IMAGEM_PADRAO }: SeoProps) {
  const tituloCompleto = title ? `${title} · ${NOME_SITE}` : NOME_SITE
  return (
    <Helmet>
      <title>{tituloCompleto}</title>
      <meta name="description" content={description} />
      <meta property="og:type" content="website" />
      <meta property="og:site_name" content={NOME_SITE} />
      <meta property="og:title" content={tituloCompleto} />
      <meta property="og:description" content={description} />
      <meta property="og:image" content={image} />
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={tituloCompleto} />
      <meta name="twitter:description" content={description} />
      <meta name="twitter:image" content={image} />
    </Helmet>
  )
}
