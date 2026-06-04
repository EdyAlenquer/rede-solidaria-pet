import { Link } from 'react-router-dom'

import { PaginaConteudo } from './PaginaConteudo'

/**
 * Página de contato com os canais de comunicação da equipe.
 *
 * O backend não expõe um endpoint de contato, portanto listamos canais reais
 * (e-mail) em vez de simular um envio que não acontece.
 *
 * @returns Página de contato com conteúdo real em PT-BR.
 */
export function ContatoPage() {
  return (
    <PaginaConteudo
      eyebrow="Fale conosco"
      titulo="Contato"
      descricao="Canais para falar com a equipe da Rede Solidária Pet."
    >
      <section className="rsp-content__section">
        <h2>Como falar com a gente</h2>
        <p>
          Estamos aqui para ajudar com dúvidas, sugestões, parcerias ou questões sobre privacidade.
          Escolha o canal mais adequado abaixo.
        </p>
      </section>

      <ul className="rsp-contato-list">
        <li className="rsp-contato-card">
          <span className="rsp-contato-card__label">Atendimento geral</span>
          <a href="mailto:contato@redesolidariapet.org.br">contato@redesolidariapet.org.br</a>
          <p>Dúvidas sobre a plataforma, sugestões e parcerias.</p>
        </li>
        <li className="rsp-contato-card">
          <span className="rsp-contato-card__label">Privacidade e dados (DPO)</span>
          <a href="mailto:privacidade@redesolidariapet.org.br">
            privacidade@redesolidariapet.org.br
          </a>
          <p>
            Para exercer seus direitos da <Link to="/privacidade">LGPD</Link> ou tirar dúvidas
            sobre tratamento de dados.
          </p>
        </li>
      </ul>

      <section className="rsp-content__section">
        <h2>Já tem conta?</h2>
        <p>
          Você pode exportar ou excluir seus dados a qualquer momento pela página de{' '}
          <Link to="/perfil">Perfil</Link>, sem precisar nos contatar.
        </p>
      </section>
    </PaginaConteudo>
  )
}
