import { Link } from 'react-router-dom'

import { PaginaConteudo } from './PaginaConteudo'

/**
 * Página institucional "Sobre" o projeto.
 *
 * Explica a missão da Rede Solidária Pet e sua relação com os Objetivos de
 * Desenvolvimento Sustentável (ODS) da ONU.
 *
 * @returns Página sobre com conteúdo real em PT-BR.
 */
export function SobrePage() {
  return (
    <PaginaConteudo
      eyebrow="O projeto"
      titulo="Sobre a Rede Solidária Pet"
      descricao="Uma rede comunitária para coordenar ajuda a animais em vulnerabilidade."
    >
      <section className="rsp-content__section">
        <h2>Nossa missão</h2>
        <p>
          A Rede Solidária Pet nasceu para organizar, em um só lugar, os pedidos de ajuda a animais
          em situação de rua ou vulnerabilidade. Protetores independentes, ONGs e voluntários muitas
          vezes se perdem entre grupos de mensagens desencontrados; aqui, cada necessidade vira um
          pedido claro, com categoria, urgência e localização aproximada, fácil de encontrar e de
          atender.
        </p>
      </section>

      <section className="rsp-content__section">
        <h2>Como ajudamos</h2>
        <ul>
          <li>Centralizamos pedidos de ração, transporte, veterinário, lar temporário e resgate.</li>
          <li>Protegemos o contato de quem publica, revelando-o só a quem quer ajudar.</li>
          <li>Registramos o histórico de atendimentos para dar transparência à rede.</li>
        </ul>
      </section>

      <section className="rsp-content__section">
        <h2>Objetivos de Desenvolvimento Sustentável (ODS)</h2>
        <p>
          O projeto se inspira nos Objetivos de Desenvolvimento Sustentável da ONU, em especial:
        </p>
        <ul>
          <li>
            <strong>ODS 11 — Cidades e comunidades sustentáveis:</strong> fortalecer redes locais
            de cuidado e convivência responsável com os animais.
          </li>
          <li>
            <strong>ODS 12 — Consumo e produção responsáveis:</strong> incentivar a doação e o
            reaproveitamento de recursos em vez do descarte.
          </li>
          <li>
            <strong>ODS 17 — Parcerias e meios de implementação:</strong> conectar pessoas, ONGs e
            voluntários em torno de uma causa comum.
          </li>
        </ul>
      </section>

      <section className="rsp-content__section">
        <h2>Faça parte</h2>
        <p>
          Você pode <Link to="/pedidos/novo">publicar um pedido</Link> ou{' '}
          <Link to="/pedidos">ajudar a comunidade</Link> agora mesmo. Toda ajuda conta.
        </p>
      </section>
    </PaginaConteudo>
  )
}
