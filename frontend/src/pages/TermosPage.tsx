import { Link } from 'react-router-dom'

import { PaginaConteudo } from './PaginaConteudo'

/**
 * Termos de Uso da Rede Solidária Pet.
 *
 * Define as regras de uso da plataforma, responsabilidades das pessoas
 * usuárias, conduta esperada e limitações.
 *
 * @returns Página de termos com conteúdo real em PT-BR.
 */
export function TermosPage() {
  return (
    <PaginaConteudo
      eyebrow="Legal"
      titulo="Termos de Uso"
      descricao="As regras para usar a Rede Solidária Pet de forma segura e respeitosa."
    >
      <p className="rsp-content__updated">Última atualização: 1º de junho de 2026.</p>

      <section className="rsp-content__section">
        <h2>Aceitação dos termos</h2>
        <p>
          Ao criar uma conta ou usar a Rede Solidária Pet, você concorda com estes Termos de Uso e
          com a nossa <Link to="/privacidade">Política de Privacidade</Link>. Se não concordar,
          por favor não utilize a plataforma.
        </p>
      </section>

      <section className="rsp-content__section">
        <h2>O que é a plataforma</h2>
        <p>
          A Rede Solidária Pet é um espaço comunitário e gratuito para divulgar pedidos de ajuda a
          animais e coordenar voluntários. Não somos uma ONG, clínica veterinária nem
          intermediários financeiros: apenas conectamos pessoas dispostas a ajudar.
        </p>
      </section>

      <section className="rsp-content__section">
        <h2>Uso da plataforma</h2>
        <ul>
          <li>Você é responsável pela veracidade das informações que publica.</li>
          <li>Use a plataforma apenas para fins legítimos de ajuda a animais.</li>
          <li>Mantenha o respeito e a cordialidade no contato com outras pessoas.</li>
          <li>Você deve ter pelo menos 18 anos para criar uma conta.</li>
        </ul>
      </section>

      <section className="rsp-content__section">
        <h2>Conduta proibida</h2>
        <ul>
          <li>Publicar conteúdo falso, enganoso, ofensivo ou ilegal.</li>
          <li>Solicitar dinheiro de forma fraudulenta ou praticar golpes.</li>
          <li>Usar os contatos de outras pessoas para spam ou fins não relacionados à ajuda.</li>
          <li>Maltratar animais ou incentivar maus-tratos.</li>
        </ul>
        <p>
          Conteúdos que violem estas regras podem ser denunciados e removidos, e contas reincidentes
          podem ser suspensas.
        </p>
      </section>

      <section className="rsp-content__section">
        <h2>Responsabilidade</h2>
        <p>
          A plataforma facilita o contato entre pessoas, mas não garante o resultado de cada pedido
          nem se responsabiliza por acordos firmados diretamente entre usuários. Avalie com cuidado
          antes de combinar transporte, doações ou resgates.
        </p>
      </section>

      <section className="rsp-content__section">
        <h2>Alterações</h2>
        <p>
          Podemos atualizar estes termos para refletir melhorias na plataforma. Mudanças
          relevantes serão comunicadas, e o uso continuado após a atualização indica concordância
          com a nova versão.
        </p>
      </section>
    </PaginaConteudo>
  )
}
