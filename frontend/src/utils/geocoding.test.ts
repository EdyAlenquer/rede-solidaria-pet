import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { buscarEndereco } from './geocoding'

/**
 * Monta uma resposta de fetch fake com o corpo JSON informado.
 *
 * @param body - Corpo a ser retornado por `response.json()`.
 * @param ok - Indica se a resposta deve ser considerada bem-sucedida.
 * @returns Objeto compatível com `Response` o suficiente para os testes.
 */
function fakeResponse(body: unknown, ok = true) {
  return {
    ok,
    json: async () => body,
  } as Response
}

const resultadoNominatim = [
  {
    display_name: 'Praça da Sé, Sé, São Paulo, Região Metropolitana de São Paulo, São Paulo, Brasil',
    lat: '-23.5503',
    lon: '-46.6339',
    address: {
      suburb: 'Sé',
      city: 'São Paulo',
      state: 'São Paulo',
    },
  },
]

describe('buscarEndereco', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('parseia resultados do Nominatim e deriva label, lat/lon, cidade, UF e bairro', async () => {
    const fetchMock = vi.fn().mockResolvedValue(fakeResponse(resultadoNominatim))
    vi.stubGlobal('fetch', fetchMock)

    const resultados = await buscarEndereco('praça da sé')

    expect(resultados).toHaveLength(1)
    expect(resultados[0]).toEqual({
      label:
        'Praça da Sé, Sé, São Paulo, Região Metropolitana de São Paulo, São Paulo, Brasil',
      latitude: -23.5503,
      longitude: -46.6339,
      cidade: 'São Paulo',
      estado: 'SP',
      bairro: 'Sé',
    })
  })

  it('chama o Nominatim com os parâmetros esperados (Brasil, PT-BR, jsonv2)', async () => {
    const fetchMock = vi.fn().mockResolvedValue(fakeResponse(resultadoNominatim))
    vi.stubGlobal('fetch', fetchMock)

    await buscarEndereco('rua das flores')

    const url = String(fetchMock.mock.calls[0]?.[0])
    expect(url).toContain('https://nominatim.openstreetmap.org/search')
    expect(url).toContain('format=jsonv2')
    expect(url).toContain('addressdetails=1')
    expect(url).toContain('countrycodes=br')
    expect(url).toContain('accept-language=pt-BR')
    expect(url).toContain('limit=5')
    expect(url).toContain('q=rua+das+flores')
  })

  it('mapeia nomes de estado para a sigla UF dos 27 estados', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      fakeResponse([
        {
          display_name: 'Centro, Belo Horizonte, Minas Gerais, Brasil',
          lat: '-19.92',
          lon: '-43.94',
          address: { neighbourhood: 'Centro', town: 'Belo Horizonte', state: 'Minas Gerais' },
        },
      ]),
    )
    vi.stubGlobal('fetch', fetchMock)

    const resultados = await buscarEndereco('centro bh')

    expect(resultados[0].estado).toBe('MG')
    expect(resultados[0].cidade).toBe('Belo Horizonte')
    expect(resultados[0].bairro).toBe('Centro')
  })

  it('omite cidade/estado/bairro quando o endereço não os traz', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      fakeResponse([
        {
          display_name: 'Algum ponto remoto, Brasil',
          lat: '-10',
          lon: '-50',
          address: { country: 'Brasil' },
        },
      ]),
    )
    vi.stubGlobal('fetch', fetchMock)

    const resultados = await buscarEndereco('ponto remoto')

    expect(resultados[0]).toEqual({
      label: 'Algum ponto remoto, Brasil',
      latitude: -10,
      longitude: -50,
    })
  })

  it('retorna [] quando a consulta é vazia, sem chamar a rede', async () => {
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)

    expect(await buscarEndereco('   ')).toEqual([])
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('retorna [] em erro de rede (o usuário ainda pode clicar no mapa)', async () => {
    const fetchMock = vi.fn().mockRejectedValue(new Error('rede caiu'))
    vi.stubGlobal('fetch', fetchMock)

    expect(await buscarEndereco('qualquer coisa')).toEqual([])
  })

  it('retorna [] quando a resposta HTTP não é ok', async () => {
    const fetchMock = vi.fn().mockResolvedValue(fakeResponse([], false))
    vi.stubGlobal('fetch', fetchMock)

    expect(await buscarEndereco('qualquer coisa')).toEqual([])
  })
})
