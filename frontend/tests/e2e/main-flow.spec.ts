import { expect, test } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

type Pedido = {
  categoria: string
  contato: string
  data_criacao: string
  descricao: string
  id: number
  status: string
  titulo: string
  urgencia: string
}

const pedidoInicial: Pedido = {
  id: 7,
  titulo: 'Gata precisa de transporte',
  descricao: 'Precisa ir até a clínica parceira para consulta.',
  categoria: 'transporte',
  urgencia: 'alta',
  status: 'aberto',
  contato: '11999990000',
  data_criacao: '2026-05-27T12:00:00',
}

/**
 * Instala mocks HTTP para o fluxo principal.
 *
 * @param page - Página Playwright sob teste.
 * @returns Estado em memória usado pelas rotas mockadas.
 */
async function mockApi(page: import('@playwright/test').Page) {
  const pedidos = [pedidoInicial]
  const atendimentos: Array<{ data_contato: string; id: number; observacao: string; pedido_id: number; tipo_ajuda: string }> = []

  await page.route(/\/api\/v1\/pedidos(?:\?.*)?$/, async (route) => {
    if (route.request().method() === 'POST') {
      const payload = await route.request().postDataJSON()
      const pedido = {
        ...payload,
        id: 8,
        status: 'aberto',
        data_criacao: '2026-05-27T13:00:00',
      }
      pedidos.push(pedido)
      await route.fulfill({ json: pedido, status: 201 })
      return
    }

    await route.fulfill({
      json: {
        items: pedidos,
        page_info: { page: 1, page_size: 20, total: pedidos.length, total_pages: 1 },
      },
    })
  })

  await page.route(/\/api\/v1\/pedidos\/\d+\/atendimentos(?:\?.*)?$/, async (route) => {
    if (route.request().method() === 'POST') {
      const payload = await route.request().postDataJSON()
      const atendimento = {
        id: 21,
        pedido_id: 8,
        tipo_ajuda: payload.tipo_ajuda,
        observacao: payload.observacao,
        data_contato: '2026-05-27T14:00:00',
      }
      atendimentos.push(atendimento)
      await route.fulfill({ json: atendimento, status: 201 })
      return
    }

    await route.fulfill({ json: atendimentos })
  })

  await page.route(/\/api\/v1\/pedidos\/\d+$/, async (route) => {
    const id = Number(route.request().url().split('/').pop())
    const pedido = pedidos.find((item) => item.id === id) ?? pedidos[0]
    await route.fulfill({ json: pedido })
  })

  await page.route('**/api/v1/doadores', async (route) => {
    const payload = await route.request().postDataJSON()
    await route.fulfill({ json: { ...payload, id: 13, email: null }, status: 201 })
  })

  return { atendimentos, pedidos }
}

test.describe('fluxo principal', () => {
  test('cadastrar, listar, detalhar e atender pedido sem expor contato antes do clique', async ({ page }) => {
    await mockApi(page)

    await page.goto('/pedidos/novo')
    await page.getByLabel('Título do pedido').fill('Ração para filhotes')
    await page.getByLabel('Categoria').selectOption('ração')
    await page.getByLabel('Urgência').selectOption('alta')
    await page.getByLabel('Descrição').fill('Família temporária precisa de ração hoje.')
    await page.getByLabel('Contato').fill('11999990000')
    await page.getByRole('button', { name: 'Publicar pedido' }).click()

    await expect(page.getByRole('heading', { name: 'Ração para filhotes' })).toBeVisible()
    await expect(page.getByText('11999990000')).toHaveCount(0)

    await page.getByRole('link', { name: 'Voltar aos pedidos' }).click()
    await expect(page.getByRole('link', { name: /ração para filhotes/i })).toBeVisible()

    await page.getByRole('link', { name: /ração para filhotes/i }).click()
    await page.getByRole('button', { name: 'Mostrar contato' }).click()
    await expect(page.getByText('11999990000')).toBeVisible()

    await page.getByRole('button', { name: 'Quero ajudar' }).click()
    await page.getByLabel('Seu nome').fill('Maria')
    await page.getByLabel('Telefone ou WhatsApp').fill('11988887777')
    await page.getByLabel('Tipo de ajuda').selectOption('ração')
    await page.getByLabel('Observação').fill('Consigo entregar hoje.')
    await page.getByRole('button', { name: 'Confirmar ajuda' }).click()

    await expect(page.getByText('Ajuda registrada. Obrigado por apoiar este pedido.')).toBeVisible()
    await expect(page.getByText('Consigo entregar hoje.')).toBeVisible()
  })
})

test.describe('acessibilidade automatizada', () => {
  for (const path of ['/', '/pedidos', '/pedidos/novo', '/pedidos/7']) {
    test(`não tem violações críticas em ${path}`, async ({ page }) => {
      await mockApi(page)
      await page.goto(path)

      const results = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze()

      expect(results.violations.filter((violation) => violation.impact === 'critical')).toEqual([])
    })
  }
})
