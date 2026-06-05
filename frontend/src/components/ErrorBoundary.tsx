import { Component, type ErrorInfo, type ReactNode } from 'react'

type ErrorBoundaryProps = {
  children: ReactNode
  /** Callback opcional acionado ao clicar em "Tentar novamente". */
  onReset?: () => void
}

type ErrorBoundaryState = {
  temErro: boolean
}

/**
 * Limite de erro que captura exceções de renderização da árvore filha.
 *
 * Exibe um fallback amigável em PT-BR com a ação "Tentar novamente", que
 * reseta o estado interno e dispara o callback `onReset` quando fornecido.
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  /**
   * Inicializa o estado do limite de erro.
   *
   * @param props - Filhos e callback opcional de reset.
   */
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { temErro: false }
  }

  /**
   * Deriva o estado de erro a partir de uma exceção lançada por um filho.
   *
   * @returns Novo estado indicando que houve erro.
   */
  static getDerivedStateFromError(): ErrorBoundaryState {
    return { temErro: true }
  }

  /**
   * Registra o erro capturado para diagnóstico.
   *
   * @param error - Erro lançado pela árvore filha.
   * @param info - Detalhes do componente onde o erro ocorreu.
   * @returns Nada. Efeito colateral: log no console.
   */
  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error('ErrorBoundary capturou um erro:', error, info)
  }

  /**
   * Reseta o estado de erro e aciona o callback de reset.
   *
   * @returns Nada. Efeito colateral: re-renderiza os filhos.
   */
  private handleReset = (): void => {
    this.setState({ temErro: false })
    this.props.onReset?.()
  }

  /**
   * Renderiza os filhos ou o fallback de erro.
   *
   * @returns Conteúdo normal ou tela de erro amigável.
   */
  render(): ReactNode {
    if (this.state.temErro) {
      return (
        <section className="rsp-page rsp-error" role="alert">
          <div className="rsp-error__box">
            <h1 className="rsp-page__title">Algo deu errado</h1>
            <p className="rsp-page__sub">
              Tivemos um problema ao exibir esta parte da página. Você pode tentar novamente.
            </p>
            <button type="button" className="rsp-btn rsp-btn--primary" onClick={this.handleReset}>
              Tentar novamente
            </button>
          </div>
        </section>
      )
    }
    return this.props.children
  }
}
