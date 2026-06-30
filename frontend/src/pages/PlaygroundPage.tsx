import { Badge, Button, Card, Input, Select } from '../components/ui'

/**
 * Galeria de exemplos dos componentes base do sistema visual.
 *
 * @returns Página de exemplos dos componentes; rota disponível apenas em desenvolvimento.
 */
export function PlaygroundPage() {
  return (
    <section className="rsp-page">
      <div className="rsp-page__header">
        <div>
          <p className="rsp-eyebrow">Sistema visual</p>
          <h1 className="rsp-page__title">Playground</h1>
          <p className="rsp-page__sub">
            Exemplos dos componentes base usados pela interface.
          </p>
        </div>
      </div>
      <div className="rsp-playground-grid">
        <Card title="Pedido em destaque">
          <p>Cadela com filhotes precisa de ração ainda hoje.</p>
          <Badge tone="danger">Urgente</Badge>
        </Card>
        <Card title="Formulário base">
          <div className="rsp-form-stack">
            <Input id="playground-bairro" label="Bairro" placeholder="Vila Esperança" />
            <Select
              id="playground-urgencia"
              label="Urgência"
              options={[
                { label: 'Alta', value: 'alta' },
                { label: 'Média', value: 'media' },
                { label: 'Baixa', value: 'baixa' },
              ]}
            />
            <Button>Salvar pedido</Button>
          </div>
        </Card>
      </div>
    </section>
  )
}
