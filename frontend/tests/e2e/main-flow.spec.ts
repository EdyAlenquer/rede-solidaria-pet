import { expect, test, type Page, type Route } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

/**
 * Forma simplificada de um pedido público, suficiente para o fluxo E2E.
 *
 * Espelha o subconjunto de `Pedido` (frontend/src/types/api.ts) usado pelas
 * telas de lista e detalhe. O `contato` nunca aparece nesta forma: ele só é
 * revelado pela rota privada `GET /pedidos/{id}/contato`.
 */
type Pedido = {
  id: number
  titulo: string
  descricao: string
  categoria: string
  urgencia: string
  status: string
  data_criacao: string
  cidade?: string
  estado?: string
  autor_id?: number
}

/** Usuário autenticado mockado (forma de `UsuarioRead`). */
const usuarioMock = {
  id: 99,
  nome: 'Voluntária Teste',
  email: 'voluntaria@exemplo.com',
  papel: 'protetor' as const,
}

/** Pedido pré-existente de outra pessoa, usado para o caminho "quero ajudar". */
const pedidoInicial: Pedido = {
  id: 7,
  titulo: 'Gata precisa de transporte',
  descricao: 'Precisa ir até a clínica parceira para uma consulta de rotina.',
  categoria: 'transporte',
  urgencia: 'alta',
  status: 'aberto',
  data_criacao: '2026-05-27T12:00:00',
  cidade: 'São Paulo',
  estado: 'SP',
  autor_id: 1,
}

/** Contato protegido devolvido apenas após login + clique explícito. */
const contatoRevelado = {
  contato: '11999990000',
  whatsapp: 'https://wa.me/5511999990000',
}

/**
 * Estado em memória compartilhado pelas rotas mockadas de um teste.
 */
type EstadoApi = {
  pedidos: Pedido[]
  atendimentos: Array<{
    id: number
    pedido_id: number
    tipo_ajuda: string
    observacao: string | null
    data_contato: string
  }>
  tokenEmitido: boolean
}

/**
 * Instala mocks HTTP para o fluxo autenticado completo.
 *
 * Cobre autenticação (registro/login/me), listagem e detalhe de pedidos,
 * criação de pedido, revelação de contato e registro de atendimento. Mantém o
 * spec determinístico e independente de um backend real (sem rate limit, sem
 * banco), seguindo o mesmo padrão de mocks já usado no projeto.
 *
 * @param page - Página Playwright sob teste.
 * @returns Estado em memória usado e mutado pelas rotas mockadas.
 */
async function mockApi(page: Page): Promise<EstadoApi> {
  const estado: EstadoApi = {
    pedidos: [pedidoInicial],
    atendimentos: [],
    tokenEmitido: false,
  }

  // Autenticação ------------------------------------------------------------
  await page.route(/\/api\/v1\/auth\/registro$/, async (route: Route) => {
    const payload = await route.request().postDataJSON()
    await route.fulfill({
      status: 201,
      json: { ...usuarioMock, email: payload.email, nome: payload.nome },
    })
  })

  await page.route(/\/api\/v1\/auth\/login$/, async (route: Route) => {
    estado.tokenEmitido = true
    await route.fulfill({
      json: { access_token: 'token-e2e-fake', token_type: 'bearer' },
    })
  })

  await page.route(/\/api\/v1\/auth\/me$/, async (route: Route) => {
    if (!estado.tokenEmitido) {
      await route.fulfill({ status: 401, json: { detail: 'Não autenticado.' } })
      return
    }
    await route.fulfill({ json: usuarioMock })
  })

  // Atendimentos (precede a rota genérica de pedido por especificidade) ------
  await page.route(/\/api\/v1\/pedidos\/\d+\/atendimentos(?:\?.*)?$/, async (route: Route) => {
    if (route.request().method() === 'POST') {
      const payload = await route.request().postDataJSON()
      const pedidoId = Number(route.request().url().match(/pedidos\/(\d+)\//)?.[1])
      const atendimento = {
        id: estado.atendimentos.length + 1,
        pedido_id: pedidoId,
        tipo_ajuda: payload.tipo_ajuda,
        observacao: payload.observacao ?? null,
        data_contato: '2026-05-27T14:00:00',
      }
      estado.atendimentos.push(atendimento)
      await route.fulfill({ json: atendimento, status: 201 })
      return
    }
    await route.fulfill({ json: estado.atendimentos })
  })

  // Contato protegido -------------------------------------------------------
  await page.route(/\/api\/v1\/pedidos\/\d+\/contato$/, async (route: Route) => {
    await route.fulfill({ json: contatoRevelado })
  })

  // Coleção de pedidos: GET (lista) e POST (criação) ------------------------
  await page.route(/\/api\/v1\/pedidos(?:\?.*)?$/, async (route: Route) => {
    if (route.request().method() === 'POST') {
      const payload = await route.request().postDataJSON()
      const pedido: Pedido = {
        ...payload,
        id: 8,
        status: 'aberto',
        data_criacao: '2026-05-27T13:00:00',
        autor_id: usuarioMock.id,
      }
      estado.pedidos.push(pedido)
      await route.fulfill({ json: pedido, status: 201 })
      return
    }
    await route.fulfill({
      json: {
        items: estado.pedidos,
        page_info: {
          page: 1,
          page_size: 20,
          total: estado.pedidos.length,
          total_pages: 1,
        },
      },
    })
  })

  // Detalhe de um pedido por id --------------------------------------------
  await page.route(/\/api\/v1\/pedidos\/\d+$/, async (route: Route) => {
    const id = Number(route.request().url().split('/').pop())
    const pedido = estado.pedidos.find((item) => item.id === id) ?? estado.pedidos[0]
    await route.fulfill({ json: pedido })
  })

  return estado
}

test.describe('fluxo autenticado principal', () => {
  test('registrar, entrar, publicar pedido, ver na lista, detalhar e ajudar', async ({ page }) => {
    await mockApi(page)

    // 1) Registrar ----------------------------------------------------------
    await page.goto('/cadastrar')
    await page.getByLabel('Nome').fill('Voluntária Teste')
    await page.getByLabel('E-mail').fill('voluntaria@exemplo.com')
    await page.getByLabel('Senha').fill('senha-super-segura')
    await page.getByLabel('Telefone (opcional)').fill('11988887777')
    await page.locator('#consentimento').check()
    await page.getByRole('button', { name: 'Criar conta' }).click()

    // O registro autentica e redireciona para a lista de pedidos.
    await expect(page.getByRole('heading', { name: 'Pedidos da comunidade' })).toBeVisible()

    // 2) Sair e entrar de novo, exercitando o login explícito ---------------
    await page.getByRole('button', { name: 'Sair' }).click()
    await page.goto('/entrar')
    await page.getByLabel('E-mail').fill('voluntaria@exemplo.com')
    await page.getByLabel('Senha').fill('senha-super-segura')
    await page.getByRole('button', { name: 'Entrar' }).click()
    await expect(page.getByRole('heading', { name: 'Pedidos da comunidade' })).toBeVisible()

    // 3) Criar um pedido com cidade/estado/consentimento --------------------
    await page.goto('/pedidos/novo')
    await expect(page.getByRole('heading', { name: 'Novo pedido' })).toBeVisible()
    await page.getByLabel('Título do pedido').fill('Ração para filhotes')
    await page.getByLabel('Descrição').fill('Família temporária precisa de ração hoje.')
    // Os selects são localizados por id: o nome acessível inclui a opção
    // selecionada (ex.: "Estado UF"), o que quebra um getByLabel exato.
    await page.locator('#categoria').selectOption('racao')
    await page.locator('#urgencia').selectOption('alta')
    await page.getByLabel('Contato').fill('11999990000')
    await page.locator('#cidade').fill('São Paulo')
    await page.locator('#estado').selectOption('SP')
    await page.locator('#consentimento').check()
    await page.getByRole('button', { name: 'Publicar pedido' }).click()

    // Vai direto ao detalhe do pedido recém-criado; contato não é exposto.
    await expect(page.getByRole('heading', { name: 'Ração para filhotes' })).toBeVisible()
    await expect(page.getByText('11999990000')).toHaveCount(0)

    // 4) Ver o pedido na lista ----------------------------------------------
    await page.getByRole('link', { name: 'Voltar aos pedidos' }).click()
    await expect(page.getByRole('heading', { name: 'Pedidos da comunidade' })).toBeVisible()
    await expect(page.getByRole('link', { name: /ração para filhotes/i })).toBeVisible()

    // 5) Abrir o detalhe de um pedido de outra pessoa e ajudar --------------
    await page.goto('/pedidos/7')
    await expect(page.getByRole('heading', { name: 'Gata precisa de transporte' })).toBeVisible()

    // Revelar contato (somente logado, após clique explícito).
    await expect(page.getByText('11999990000')).toHaveCount(0)
    await page.getByRole('button', { name: 'Revelar contato' }).click()
    await expect(page.getByText('11999990000')).toBeVisible()

    // "Quero ajudar" registra um atendimento sem expor o doador.
    await page.getByRole('button', { name: 'Quero ajudar' }).click()
    await page.locator('#tipo-ajuda').selectOption('transporte')
    await page.getByLabel('Observação').fill('Posso levar até a clínica amanhã.')
    await page.getByRole('button', { name: 'Confirmar ajuda' }).click()

    await expect(
      page.getByText('Ajuda registrada. Obrigado por apoiar este pedido!'),
    ).toBeVisible()
    await expect(page.getByText('Posso levar até a clínica amanhã.')).toBeVisible()
  })
})

test.describe('acessibilidade automatizada', () => {
  // Rotas públicas e as novas páginas autenticáveis devem passar no axe.
  const rotas = ['/', '/pedidos', '/pedidos/7', '/entrar', '/cadastrar', '/privacidade']

  for (const path of rotas) {
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
