import { describe, expect, it, vi } from 'vitest'
import { definirDadosIniciais } from '../../src/services/cache.js'
import { apiBaixar, apiGet, definirFalhaSimulada, ErroApi, montarUrl } from '../../src/services/http.js'

const BASE = 'http://api.teste'

describe('montarUrl', () => {
  it('junta caminho e parâmetros', () => {
    expect(montarUrl('/projecoes', { ano: 2070, recorte: 'chefe_60_mais' }, BASE)).toBe(
      'http://api.teste/projecoes?ano=2070&recorte=chefe_60_mais',
    )
  })
  it('ignora parâmetros nulos ou indefinidos', () => {
    expect(montarUrl('/x', { a: null, b: undefined, c: 0 }, BASE)).toBe('http://api.teste/x?c=0')
  })
})

describe('apiGet', () => {
  it('devolve o JSON quando a resposta é bem-sucedida', async () => {
    const fetcher = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({ ok: 1 }) })
    await expect(apiGet('/x', {}, { fetcher, base: BASE })).resolves.toEqual({ ok: 1 })
    expect(fetcher).toHaveBeenCalledWith('http://api.teste/x', { signal: undefined })
  })
  it('converte código de erro HTTP em ErroApi com o status', async () => {
    const fetcher = vi.fn().mockResolvedValue({ ok: false, status: 422 })
    await expect(apiGet('/x', {}, { fetcher, base: BASE })).rejects.toMatchObject({ name: 'ErroApi', status: 422 })
  })
  it('converte falha de rede em ErroApi com status 0', async () => {
    const fetcher = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'))
    const erro = await apiGet('/x', {}, { fetcher, base: BASE }).catch((e) => e)
    expect(erro).toBeInstanceOf(ErroApi)
    expect(erro.status).toBe(0)
  })
  it('repassa o cancelamento sem transformar em erro de conexão', async () => {
    const abort = Object.assign(new Error('cancelado'), { name: 'AbortError' })
    const fetcher = vi.fn().mockRejectedValue(abort)
    await expect(apiGet('/x', {}, { fetcher, base: BASE })).rejects.toBe(abort)
  })
})

describe('apiBaixar', () => {
  it('devolve o blob e extrai o nome do arquivo do cabeçalho Content-Disposition', async () => {
    const blob = new Blob(['a,b'])
    const headers = new Headers({ 'content-disposition': 'attachment; filename="proced_Brasil_2050.csv"' })
    const fetcher = vi.fn().mockResolvedValue({ ok: true, headers, blob: () => Promise.resolve(blob) })
    await expect(apiBaixar('/exportar', { formato: 'csv' }, { fetcher, base: BASE })).resolves.toEqual({
      blob,
      nomeArquivo: 'proced_Brasil_2050.csv',
    })
  })
})

describe('apiGet com cache', () => {
  const ok = (corpo) => vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve(corpo) })

  it('a mesma consulta só vai à API uma vez', async () => {
    const fetcher = ok({ v: 1 })
    await apiGet('/x', { a: 1, b: 2 }, { fetcher, base: BASE })
    await expect(apiGet('/x', { b: 2, a: 1 }, { fetcher, base: BASE })).resolves.toEqual({ v: 1 })
    expect(fetcher).toHaveBeenCalledTimes(1)
  })

  it('parâmetros diferentes são consultas diferentes', async () => {
    const fetcher = ok({})
    await apiGet('/x', { localidade: 'Brasil' }, { fetcher, base: BASE })
    await apiGet('/x', { localidade: 'PE' }, { fetcher, base: BASE })
    expect(fetcher).toHaveBeenCalledTimes(2)
  })

  it('cache: false sempre vai à API', async () => {
    const fetcher = ok({})
    await apiGet('/x', {}, { fetcher, base: BASE })
    await apiGet('/x', {}, { fetcher, base: BASE, cache: false })
    expect(fetcher).toHaveBeenCalledTimes(2)
  })

  it('recalcular (RF09) nunca usa nem grava o cache', async () => {
    const fetcher = ok({})
    await apiGet('/simulador', { ano: 2050, recalcular: true }, { fetcher, base: BASE })
    await apiGet('/simulador', { ano: 2050, recalcular: true }, { fetcher, base: BASE })
    expect(fetcher).toHaveBeenCalledTimes(2)
  })

  it('erro não fica guardado: a nova tentativa vai à API', async () => {
    const fetcher = vi.fn()
      .mockResolvedValueOnce({ ok: false, status: 503 })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ v: 2 }) })
    await expect(apiGet('/x', {}, { fetcher, base: BASE })).rejects.toMatchObject({ status: 503 })
    await expect(apiGet('/x', {}, { fetcher, base: BASE })).resolves.toEqual({ v: 2 })
  })

  it('responde com os dados de abertura sem chamar a API', async () => {
    definirDadosIniciais({ '/projecoes/serie?k=1&recorte=a': { de: 'abertura' } })
    const fetcher = ok({})
    await expect(apiGet('/projecoes/serie', { recorte: 'a', k: 1 }, { fetcher, base: BASE })).resolves.toEqual({ de: 'abertura' })
    expect(fetcher).not.toHaveBeenCalled()
  })

  it('a falha simulada do menu Demonstração vale mesmo com a consulta guardada', async () => {
    const fetcher = ok({})
    await apiGet('/x', {}, { fetcher, base: BASE })
    definirFalhaSimulada(true)
    try {
      await expect(apiGet('/x', {}, { fetcher, base: BASE })).rejects.toMatchObject({ name: 'ErroApi', status: 0 })
    } finally {
      definirFalhaSimulada(false)
    }
  })
})
