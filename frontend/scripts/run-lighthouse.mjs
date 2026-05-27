import http from 'node:http'
import { spawn, spawnSync } from 'node:child_process'
import { once } from 'node:events'
import lighthouse from 'lighthouse'
import { launch } from 'chrome-launcher'

const HOST = '127.0.0.1'
const API_PORT = 45891
const APP_PORT = 56310
const APP_ORIGIN = `http://${HOST}:${APP_PORT}`

const pedido = {
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
 * Escreve uma resposta JSON no servidor mock.
 *
 * @param {http.ServerResponse} response - Resposta HTTP a preencher.
 * @param {unknown} body - Corpo serializável como JSON.
 * @param {number} status - Código HTTP de resposta.
 * @returns {void}
 */
function writeJson(response, body, status = 200) {
  response.writeHead(status, { 'content-type': 'application/json' })
  response.end(JSON.stringify(body))
}

/**
 * Cria uma API mock mínima para as rotas usadas pelas telas principais.
 *
 * @returns {http.Server} Servidor HTTP configurado.
 */
function createApiServer() {
  return http.createServer((request, response) => {
    const url = new URL(request.url ?? '/', `http://${HOST}:${API_PORT}`)
    if (url.pathname === '/api/v1/pedidos') {
      writeJson(response, {
        items: [pedido],
        page_info: { page: 1, page_size: 20, total: 1, total_pages: 1 },
      })
      return
    }
    if (url.pathname === '/api/v1/pedidos/7') {
      writeJson(response, pedido)
      return
    }
    if (url.pathname === '/api/v1/pedidos/7/atendimentos') {
      writeJson(response, [])
      return
    }
    writeJson(response, { detail: 'Not Found' }, 404)
  })
}

/**
 * Aguarda uma URL responder com HTTP 200.
 *
 * @param {string} url - URL absoluta a consultar.
 * @returns {Promise<void>} Resolve quando a URL fica disponível.
 */
async function waitForOk(url) {
  const deadline = Date.now() + 30_000
  while (Date.now() < deadline) {
    try {
      const response = await fetch(url)
      if (response.ok) return
    } catch {
      // Servidor ainda inicializando.
    }
    await new Promise((resolve) => setTimeout(resolve, 500))
  }
  throw new Error(`Timeout aguardando ${url}`)
}

/**
 * Gera o build de produção que será auditado.
 *
 * @returns {void}
 */
function buildApp() {
  const result = spawnSync('npm', ['run', 'build'], {
    env: process.env,
    stdio: 'inherit',
  })
  if (result.status !== 0) {
    throw new Error('Build de produção falhou antes do Lighthouse')
  }
}

/**
 * Inicia o preview do Vite apontando para a API mock.
 *
 * @returns {import('node:child_process').ChildProcess} Processo do Vite.
 */
function startPreview() {
  return spawn('npm', ['run', 'preview', '--', '--host', HOST, '--port', String(APP_PORT), '--strictPort'], {
    env: {
      ...process.env,
      VITE_API_PROXY_TARGET: `http://${HOST}:${API_PORT}`,
    },
    stdio: 'inherit',
  })
}

/**
 * Executa Lighthouse mobile para uma rota da aplicação.
 *
 * @param {string} path - Rota client-side da aplicação.
 * @returns {Promise<{ accessibility: number, performance: number }>} Pontuações de 0 a 1.
 */
async function auditPath(path) {
  const chrome = await launch({ chromeFlags: ['--headless'] })
  try {
    const result = await lighthouse(`${APP_ORIGIN}${path}`, {
      port: chrome.port,
      onlyCategories: ['performance', 'accessibility'],
      output: 'json',
      logLevel: 'error',
      screenEmulation: {
        mobile: true,
        width: 390,
        height: 844,
        deviceScaleFactor: 2,
        disabled: false,
      },
      throttlingMethod: 'simulate',
    })
    if (!result?.lhr) throw new Error(`Lighthouse não retornou resultado para ${path}`)
    return {
      performance: result.lhr.categories.performance.score ?? 0,
      accessibility: result.lhr.categories.accessibility.score ?? 0,
    }
  } finally {
    await chrome.kill()
  }
}

/**
 * Executa a auditoria Lighthouse completa da Fase 7.
 *
 * @returns {Promise<void>} Resolve quando todas as rotas passam nos limiares.
 */
async function main() {
  const apiServer = createApiServer()
  apiServer.listen(API_PORT, HOST)
  await once(apiServer, 'listening')
  buildApp()
  const vite = startPreview()

  try {
    await waitForOk(APP_ORIGIN)
    const paths = ['/', '/pedidos', '/pedidos/novo', '/pedidos/7']
    const results = []
    for (const path of paths) {
      const scores = await auditPath(path)
      results.push({ path, ...scores })
    }

    for (const result of results) {
      const performance = Math.round(result.performance * 100)
      const accessibility = Math.round(result.accessibility * 100)
      console.log(`${result.path}: performance=${performance} accessibility=${accessibility}`)
      if (performance < 80 || accessibility < 90) {
        throw new Error(`Lighthouse abaixo da meta em ${result.path}`)
      }
    }
  } finally {
    vite.kill()
    apiServer.close()
  }
}

await main()
