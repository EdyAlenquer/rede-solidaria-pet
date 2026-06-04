import { useEffect, useRef, useState, type ChangeEvent } from 'react'

export type ArquivoSelecionado = {
  /** Identificador estável para a key do React e remoção. */
  id: string
  arquivo: File
  /** URL de objeto para preview (revogada ao remover/desmontar). */
  preview: string
}

type UploadImagensProps = {
  id: string
  label: string
  /** Arquivos atualmente selecionados. */
  arquivos: ArquivoSelecionado[]
  /** Reporta a nova lista de arquivos após adicionar ou remover. */
  onChange: (arquivos: ArquivoSelecionado[]) => void
  /** Tipos MIME aceitos. */
  accept?: string
}

const TIPOS_PADRAO = 'image/jpeg,image/png,image/webp'

let contador = 0
function novoId(): string {
  contador += 1
  return `img-${contador}-${Date.now()}`
}

/**
 * Campo de upload de imagens com preview e remoção individual.
 *
 * Acumula seleções (cada escolha adiciona aos arquivos já presentes) e gera
 * URLs de objeto para preview, revogadas ao remover ou desmontar para evitar
 * vazamento de memória. Não envia nada à API: apenas coleta os arquivos para
 * o formulário fazer o upload após criar o pedido.
 *
 * @param props - Identificador, label, arquivos atuais e callback de mudança.
 * @returns Campo de seleção de imagens com galeria de preview.
 */
export function UploadImagens({
  id,
  label,
  arquivos,
  onChange,
  accept = TIPOS_PADRAO,
}: UploadImagensProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [erro, setErro] = useState<string | null>(null)

  // Revoga todas as URLs de preview ao desmontar para liberar memória.
  useEffect(() => {
    return () => {
      arquivos.forEach((item) => URL.revokeObjectURL(item.preview))
    }
    // Intencional: revoga apenas no unmount; a remoção individual já revoga.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function handleChange(event: ChangeEvent<HTMLInputElement>) {
    const selecionados = Array.from(event.target.files ?? [])
    if (selecionados.length === 0) {
      return
    }
    const aceitos = accept.split(',').map((tipo) => tipo.trim())
    const validos = selecionados.filter((arquivo) => aceitos.includes(arquivo.type))
    if (validos.length < selecionados.length) {
      setErro('Apenas imagens JPG, PNG ou WebP são aceitas.')
    } else {
      setErro(null)
    }
    const novos: ArquivoSelecionado[] = validos.map((arquivo) => ({
      id: novoId(),
      arquivo,
      preview: URL.createObjectURL(arquivo),
    }))
    onChange([...arquivos, ...novos])
    // Permite reselecionar o mesmo arquivo após removê-lo.
    if (inputRef.current) {
      inputRef.current.value = ''
    }
  }

  function remover(idArquivo: string) {
    const alvo = arquivos.find((item) => item.id === idArquivo)
    if (alvo) {
      URL.revokeObjectURL(alvo.preview)
    }
    onChange(arquivos.filter((item) => item.id !== idArquivo))
  }

  return (
    <div className="rsp-upload rsp-field-wrap">
      <label className="rsp-field" htmlFor={id}>
        <span>{label}</span>
        <input
          ref={inputRef}
          id={id}
          type="file"
          className="rsp-input rsp-upload__input"
          accept={accept}
          multiple
          onChange={handleChange}
        />
      </label>
      {erro && (
        <span className="rsp-field__erro" role="alert">
          {erro}
        </span>
      )}
      {arquivos.length > 0 && (
        <ul className="rsp-upload__previews" aria-label="Imagens selecionadas">
          {arquivos.map((item) => (
            <li key={item.id} className="rsp-upload__preview">
              <img src={item.preview} alt={item.arquivo.name} />
              <button
                type="button"
                className="rsp-upload__remove"
                aria-label={`Remover ${item.arquivo.name}`}
                onClick={() => remover(item.id)}
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
