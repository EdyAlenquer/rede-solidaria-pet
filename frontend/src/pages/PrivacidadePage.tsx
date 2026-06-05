import { Link } from 'react-router-dom'

import { PaginaConteudo } from './PaginaConteudo'

/**
 * Política de Privacidade alinhada à LGPD (Lei nº 13.709/2018).
 *
 * Descreve finalidade, base legal, dados coletados, direitos do titular,
 * retenção e canal de contato/DPO.
 *
 * @returns Página de privacidade com conteúdo real em PT-BR.
 */
export function PrivacidadePage() {
  return (
    <PaginaConteudo
      eyebrow="Legal"
      titulo="Política de Privacidade"
      descricao="Como a Rede Solidária Pet trata seus dados pessoais conforme a LGPD."
    >
      <p className="rsp-content__updated">Última atualização: 1º de junho de 2026.</p>

      <section className="rsp-content__section">
        <h2>Quem somos</h2>
        <p>
          A Rede Solidária Pet é uma plataforma comunitária, sem fins lucrativos, que conecta
          protetores independentes, ONGs e voluntários para coordenar pedidos de ajuda a animais
          em situação de rua ou vulnerabilidade. Esta política explica de forma transparente como
          tratamos os dados pessoais de quem usa a plataforma.
        </p>
      </section>

      <section className="rsp-content__section">
        <h2>Finalidade e base legal</h2>
        <p>
          Tratamos dados pessoais com a finalidade de viabilizar a publicação de pedidos de ajuda,
          permitir o contato entre quem precisa e quem pode ajudar e manter o histórico de
          atendimentos. Esse tratamento é feito com base no seu{' '}
          <strong>consentimento</strong> (art. 7º, I) e no{' '}
          <strong>legítimo interesse</strong> em manter uma rede de ajuda segura, conforme a{' '}
          <strong>Lei Geral de Proteção de Dados (Lei nº 13.709/2018)</strong>.
        </p>
      </section>

      <section className="rsp-content__section">
        <h2>Dados que coletamos</h2>
        <ul>
          <li>
            <strong>Nome</strong> — para identificar quem publica e coordena pedidos.
          </li>
          <li>
            <strong>E-mail</strong> — para autenticação da conta e comunicações da plataforma.
          </li>
          <li>
            <strong>Contato</strong> (telefone/WhatsApp) — revelado apenas a pessoas autenticadas
            que abrem um pedido para ajudar.
          </li>
          <li>
            <strong>Localização aproximada</strong> — cidade, estado e, opcionalmente, bairro ou
            um ponto aproximado no mapa, para situar o pedido. Não rastreamos sua localização em
            tempo real.
          </li>
          <li>
            <strong>Fotos</strong> — imagens do animal ou da situação, enviadas voluntariamente
            por quem cria o pedido.
          </li>
        </ul>
      </section>

      <section className="rsp-content__section">
        <h2>Compartilhamento</h2>
        <p>
          Não vendemos dados pessoais. O título, a descrição, a localização aproximada e as fotos
          de um pedido são públicos, pois é assim que a comunidade encontra quem precisa de ajuda.
          O seu contato direto só é exibido a usuários autenticados que demonstram intenção de
          ajudar em um pedido específico.
        </p>
      </section>

      <section className="rsp-content__section">
        <h2>Seus direitos</h2>
        <p>
          Como titular dos dados, você pode, a qualquer momento, exercer os direitos previstos na
          LGPD, incluindo confirmação do tratamento, acesso, correção e exclusão dos seus dados.
        </p>
        <ul>
          <li>
            <strong>Acesso e portabilidade</strong> — exporte uma cópia dos seus dados pela página
            de <Link to="/perfil">Perfil</Link>.
          </li>
          <li>
            <strong>Exclusão</strong> — exclua sua conta e seus dados diretamente pelo{' '}
            <Link to="/perfil">Perfil</Link>. A exclusão é irreversível.
          </li>
          <li>
            <strong>Correção</strong> — edite seus pedidos ou solicite ajustes pelos nossos canais
            de <Link to="/contato">contato</Link>.
          </li>
        </ul>
      </section>

      <section className="rsp-content__section">
        <h2>Retenção</h2>
        <p>
          Mantemos seus dados enquanto sua conta estiver ativa ou pelo tempo necessário para
          cumprir as finalidades descritas. Ao excluir a conta, seus dados pessoais são removidos,
          ressalvadas as obrigações legais de guarda quando aplicáveis.
        </p>
      </section>

      <section className="rsp-content__section">
        <h2>Contato e encarregado (DPO)</h2>
        <p>
          Para dúvidas sobre privacidade ou para exercer seus direitos, fale com o nosso
          encarregado de dados pelo e-mail{' '}
          <a href="mailto:privacidade@redesolidariapet.org.br">
            privacidade@redesolidariapet.org.br
          </a>{' '}
          ou pelos canais da página de <Link to="/contato">contato</Link>.
        </p>
      </section>
    </PaginaConteudo>
  )
}
