import { useId } from 'react'

import { PaginaConteudo } from './PaginaConteudo'

type PerguntaFaq = {
  /** Pergunta exibida no resumo. */
  pergunta: string
  /** Resposta exibida ao expandir. */
  resposta: string
}

const perguntas: PerguntaFaq[] = [
  {
    pergunta: 'Como publico um pedido de ajuda?',
    resposta:
      'Crie uma conta gratuita, clique em "Cadastrar pedido", descreva a necessidade do animal, escolha a categoria e a urgência, informe cidade e estado e, se quiser, adicione fotos. Seu contato fica protegido e só é mostrado a quem deseja ajudar.',
  },
  {
    pergunta: 'Preciso ter conta para ver os pedidos?',
    resposta:
      'Não. Qualquer pessoa pode navegar e filtrar os pedidos publicados. A conta é necessária apenas para publicar pedidos, oferecer ajuda e ver o contato direto de quem precisa.',
  },
  {
    pergunta: 'Como o meu contato é protegido?',
    resposta:
      'O contato que você cadastra não aparece publicamente no pedido. Ele só é revelado a usuários autenticados que abrem o pedido com a intenção de ajudar.',
  },
  {
    pergunta: 'O que faço se encontrar um pedido suspeito?',
    resposta:
      'Use o botão de denúncia disponível na página do pedido. Você pode indicar o motivo (spam, golpe, conteúdo impróprio ou outro) e nossa equipe avalia o caso.',
  },
  {
    pergunta: 'Como excluo a minha conta e meus dados?',
    resposta:
      'Acesse a página de Perfil. Lá você pode exportar uma cópia dos seus dados ou excluir definitivamente sua conta, conforme seus direitos na LGPD.',
  },
]

/**
 * Página de Perguntas Frequentes (FAQ).
 *
 * Cada item é um `<details>`/`<summary>` acessível, agrupado por `role="group"`
 * com nome acessível vindo da pergunta, para teclado e leitores de tela.
 *
 * @returns Página de FAQ com conteúdo real em PT-BR.
 */
export function FaqPage() {
  return (
    <PaginaConteudo
      eyebrow="Ajuda"
      titulo="Perguntas frequentes"
      descricao="Tire suas dúvidas sobre como usar a Rede Solidária Pet."
    >
      <div className="rsp-faq">
        {perguntas.map((item) => (
          <FaqItem key={item.pergunta} pergunta={item.pergunta} resposta={item.resposta} />
        ))}
      </div>
    </PaginaConteudo>
  )
}

/**
 * Item individual do FAQ com pergunta expansível.
 *
 * @param props - Pergunta e resposta do item.
 * @returns Bloco `<details>` acessível e nomeado.
 */
function FaqItem({ pergunta, resposta }: PerguntaFaq) {
  const tituloId = useId()
  return (
    <details className="rsp-faq__item" role="group" aria-labelledby={tituloId}>
      <summary className="rsp-faq__pergunta" id={tituloId}>
        {pergunta}
      </summary>
      <p className="rsp-faq__resposta">{resposta}</p>
    </details>
  )
}
