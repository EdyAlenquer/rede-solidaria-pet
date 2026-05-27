const frontendUrl = normalizeUrl(process.env.FRONTEND_PUBLIC_URL)
const backendUrl = normalizeUrl(process.env.BACKEND_PUBLIC_URL)

/**
 * Normaliza e valida URL pública HTTPS.
 *
 * @param {string | undefined} value - URL recebida por variável de ambiente.
 * @returns {URL} URL HTTPS validada.
 */
function normalizeUrl(value) {
  if (!value) {
    throw new Error('FRONTEND_PUBLIC_URL e BACKEND_PUBLIC_URL são obrigatórias.')
  }
  const url = new URL(value)
  if (url.protocol !== 'https:') {
    throw new Error(`${url.href} precisa usar HTTPS.`)
  }
  return url
}

/**
 * Busca JSON e valida status 2xx.
 *
 * @param {URL} url - Endpoint absoluto.
 * @returns {Promise<unknown>} Corpo JSON retornado.
 */
async function fetchJson(url) {
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`${url.href} retornou HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * Busca HTML e valida status 2xx.
 *
 * @param {URL} url - Página absoluta.
 * @returns {Promise<string>} Corpo HTML retornado.
 */
async function fetchText(url) {
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`${url.href} retornou HTTP ${response.status}`)
  }
  return response.text()
}

/**
 * Monta uma URL relativa preservando origem.
 *
 * @param {URL} base - URL base pública.
 * @param {string} path - Caminho absoluto.
 * @returns {URL} URL final.
 */
function withPath(base, path) {
  return new URL(path, base)
}

const health = await fetchJson(withPath(backendUrl, '/health'))
if (health.status !== 'ok') {
  throw new Error('/health não retornou {"status":"ok"}.')
}

const pedidos = await fetchJson(withPath(backendUrl, '/api/v1/pedidos'))
if (!Array.isArray(pedidos.items) || !pedidos.page_info) {
  throw new Error('/api/v1/pedidos não retornou paginação esperada.')
}

const home = await fetchText(frontendUrl)
if (!home.includes('Rede Solidária Pet') && !home.includes('<div id="root"></div>')) {
  throw new Error('Frontend público não parece servir a aplicação Vite.')
}

console.log(`Smoke OK: ${frontendUrl.href} + ${backendUrl.href}`)
