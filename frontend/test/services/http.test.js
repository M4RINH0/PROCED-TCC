import { describe, expect, it, vi } from 'vitest'
import { apiBaixar, apiGet, ErroApi, montarUrl } from '../../src/services/http.js'

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
