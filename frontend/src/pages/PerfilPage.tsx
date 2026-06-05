import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'
import { Badge, Button, Input, Modal } from '../components/ui'
import { Seo } from '../components/Seo'
import { useToast } from '../components/Toast'
import { categorias, rotuloDe, status as statusOpcoes, urgencias } from '../constants/dominio'
import { eliminarMinhaConta, exportarMeusDados } from '../services/api/me'
import { rotuloLocalizacao, tomUrgencia } from '../utils/pedido'
import type { MeusDados } from '../types/api'

const CONFIRMACAO_EXCLUSAO = 'EXCLUIR'

/**
 * Página de perfil do usuário autenticado (`/perfil`).
 *
 * Mostra os dados da conta, lista os pedidos do usuário, permite exportar os
 * dados pessoais (download JSON, direito de acesso LGPD) e excluir a conta
 * (direito de eliminação, com confirmação forte por digitação e logout).
 *
 * @returns Tela de perfil integrada à API.
 */
export function PerfilPage() {
  const { usuario, logout } = useAuth()
  const { mostrar } = useToast()
  const navigate = useNavigate()

  const [dados, setDados] = useState<MeusDados | null>(null)
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState<string | null>(null)
  const [exportando, setExportando] = useState(false)
  const [confirmandoExclusao, setConfirmandoExclusao] = useState(false)
  const [confirmacaoTexto, setConfirmacaoTexto] = useState('')
  const [excluindo, setExcluindo] = useState(false)

  useEffect(() => {
    let ativo = true
    setCarregando(true)
    setErro(null)
    exportarMeusDados()
      .then((resposta) => {
        if (ativo) {
          setDados(resposta)
          setCarregando(false)
        }
      })
      .catch(() => {
        if (ativo) {
          setErro('Não foi possível carregar seus dados.')
          setCarregando(false)
        }
      })
    return () => {
      ativo = false
    }
  }, [])

  async function handleExportar() {
    setExportando(true)
    try {
      const meusDados = await exportarMeusDados()
      const blob = new Blob([JSON.stringify(meusDados, null, 2)], {
        type: 'application/json',
      })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = 'meus-dados-rede-solidaria-pet.json'
      document.body.appendChild(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(url)
      mostrar('Seus dados foram exportados.', 'sucesso')
    } catch {
      mostrar('Não foi possível exportar seus dados.', 'erro')
    } finally {
      setExportando(false)
    }
  }

  async function handleExcluirConta() {
    setExcluindo(true)
    try {
      await eliminarMinhaConta()
      logout()
      mostrar('Sua conta foi excluída.', 'sucesso')
      navigate('/')
    } catch {
      mostrar('Não foi possível excluir sua conta. Tente novamente.', 'erro')
      setExcluindo(false)
    }
  }

  const pedidos = dados?.pedidos ?? []

  return (
    <section className="rsp-page rsp-perfil">
      <Seo title="Meu perfil" description="Sua conta, seus pedidos e seus dados pessoais." />
      <div className="rsp-page__header">
        <div>
          <p className="rsp-eyebrow">Sua conta</p>
          <h1 className="rsp-page__title">Meu perfil</h1>
          <p className="rsp-page__sub">Gerencie sua conta, seus pedidos e seus dados.</p>
        </div>
      </div>

      <div className="rsp-card rsp-perfil__dados">
        <h2 className="rsp-block-label">Dados da conta</h2>
        {usuario && (
          <dl className="rsp-deflist">
            <div>
              <dt>Nome</dt>
              <dd>{usuario.nome}</dd>
            </div>
            <div>
              <dt>E-mail</dt>
              <dd>{usuario.email}</dd>
            </div>
            <div>
              <dt>Papel</dt>
              <dd>{usuario.papel === 'admin' ? 'Administrador' : 'Protetor'}</dd>
            </div>
          </dl>
        )}
        <div className="rsp-perfil__acoes">
          <Button variant="secondary" onClick={handleExportar} disabled={exportando}>
            {exportando ? 'Exportando...' : 'Exportar meus dados'}
          </Button>
          <Button
            variant="ghost"
            className="rsp-btn--danger"
            onClick={() => {
              setConfirmacaoTexto('')
              setConfirmandoExclusao(true)
            }}
          >
            Excluir minha conta
          </Button>
        </div>
      </div>

      <section className="rsp-detail__section" aria-labelledby="meus-pedidos-title">
        <h2 id="meus-pedidos-title" className="rsp-block-label">
          Meus pedidos
        </h2>
        {carregando && (
          <div className="rsp-skeleton" role="status">
            Carregando seus pedidos...
          </div>
        )}
        {erro && (
          <div className="rsp-empty" role="alert">
            {erro}
          </div>
        )}
        {!carregando && !erro && pedidos.length === 0 && (
          <div className="rsp-empty">
            <p>Você ainda não publicou nenhum pedido.</p>
            <Link className="rsp-btn rsp-btn--primary" to="/pedidos/novo">
              Publicar um pedido
            </Link>
          </div>
        )}
        {!carregando && !erro && pedidos.length > 0 && (
          <ul className="rsp-stack">
            {pedidos.map((pedido) => {
              const localizacao = rotuloLocalizacao(pedido)
              return (
                <li className="rsp-card rsp-perfil__pedido" key={pedido.id}>
                  <div className="rsp-perfil__pedido-head">
                    <Link className="rsp-textlink" to={`/pedidos/${pedido.id}`}>
                      {pedido.titulo}
                    </Link>
                    <Link className="rsp-textlink" to={`/pedidos/${pedido.id}/editar`}>
                      Editar
                    </Link>
                  </div>
                  <div className="rsp-meta-row">
                    <Badge tone={tomUrgencia(pedido.urgencia)}>
                      {rotuloDe(urgencias, pedido.urgencia)}
                    </Badge>
                    <Badge tone="neutral">{rotuloDe(statusOpcoes, pedido.status)}</Badge>
                    <Badge tone="neutral">{rotuloDe(categorias, pedido.categoria)}</Badge>
                    {localizacao && <Badge tone="neutral">{localizacao}</Badge>}
                  </div>
                </li>
              )
            })}
          </ul>
        )}
      </section>

      <Modal
        open={confirmandoExclusao}
        onClose={() => setConfirmandoExclusao(false)}
        titulo="Excluir minha conta"
        rodape={
          <>
            <Button variant="secondary" onClick={() => setConfirmandoExclusao(false)}>
              Cancelar
            </Button>
            <Button
              className="rsp-btn--danger"
              onClick={handleExcluirConta}
              disabled={confirmacaoTexto.trim().toUpperCase() !== CONFIRMACAO_EXCLUSAO || excluindo}
            >
              {excluindo ? 'Excluindo...' : 'Excluir conta'}
            </Button>
          </>
        }
      >
        <p>
          Esta ação é <strong>permanente</strong> e remove seus dados pessoais, conforme a LGPD.
          Seus pedidos serão anonimizados.
        </p>
        <p>
          Para confirmar, digite <strong>{CONFIRMACAO_EXCLUSAO}</strong> no campo abaixo.
        </p>
        <Input
          id="confirmacao-exclusao"
          label={`Digite ${CONFIRMACAO_EXCLUSAO} para confirmar`}
          value={confirmacaoTexto}
          onChange={(event) => setConfirmacaoTexto(event.target.value)}
          autoComplete="off"
        />
      </Modal>
    </section>
  )
}
