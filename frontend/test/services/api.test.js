import { describe, expect, it, vi } from 'vitest'
import { valoresDoCenario } from '../../src/utils/series.js'
import { aquecerApi, buscarSerie, exportarDados } from '../../src/services/api.js'
import { guardarCache } from '../../src/services/cache.js'

describe('buscarSerie', () => {
  it('chama GET /projecoes/serie com o recorte', async () => {
    const fetcher = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({}) })
    await buscarSerie({ recorte: 'chefe_60_mais' }, { fetcher, base: 'http://api' })
    expect(fetcher.mock.calls[0][0]).toBe('http://api/projecoes/serie?recorte=chefe_60_mais')
  })
})

describe('exportarDados', () => {
  it('chama GET /exportar com os parâmetros informados', async () => {
    const fetcher = vi.fn().mockResolvedValue({ ok: true, blob: () => Promise.resolve(new Blob()) })
    await exportarDados({ formato: 'xlsx', escopo: 'serie', ano: 2050, localidade: 'Brasil', intensidade: 0.6, k: 1 }, { fetcher, base: 'http://api' })
    expect(fetcher.mock.calls[0][0]).toBe('http://api/exportar?formato=xlsx&escopo=serie&ano=2050&localidade=Brasil&intensidade=0.6&k=1')
  })
})

describe('valoresDoCenario', () => {
  it('extrai o valor de um cenário em cada ano, mantendo os nulos', () => {
    const pontos = [
      { ano: 2070, cenarios: [{ id: 'ibge', valor: 94.6 }] },
      { ano: 2069, cenarios: [{ id: 'ibge', valor: null }] },
    ]
    expect(valoresDoCenario(pontos, 'ibge')).toEqual([
      { ano: 2070, valor: 94.6 },
      { ano: 2069, valor: null },
    ])
    expect(valoresDoCenario(pontos, 'mod')).toEqual([
      { ano: 2070, valor: null },
      { ano: 2069, valor: null },
    ])
  })
})

describe('aquecerApi', () => {
  it('chama as consultas que carregam todas as tabelas da API', async () => {
    const fetcher = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({}) })
    await aquecerApi({ fetcher, base: 'http://api' })
    const urls = fetcher.mock.calls.map(([url]) => url)
    expect(urls).toHaveLength(2)
    expect(urls.some((u) => u.startsWith('http://api/projecoes/serie?'))).toBe(true)
    expect(urls.some((u) => u.startsWith('http://api/estrutura-etaria/piramides?'))).toBe(true)
  })

  it('vai à API mesmo com as respostas já guardadas', async () => {
    guardarCache('/estrutura-etaria/piramides?k=1&localidade=Brasil', {})
    guardarCache('/projecoes/serie?intensidade=0.6&k=1&localidade=Brasil&recorte=todos_domicilios', {})
    const fetcher = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({}) })
    await aquecerApi({ fetcher, base: 'http://api' })
    expect(fetcher).toHaveBeenCalledTimes(2)
  })

  it('ignora erros: a API fora do ar não quebra a abertura', async () => {
    const fetcher = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'))
    const resultados = await aquecerApi({ fetcher, base: 'http://api' })
    expect(resultados.every((r) => r.status === 'rejected')).toBe(true)
  })
})
