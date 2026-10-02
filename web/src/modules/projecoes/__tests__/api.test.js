import { describe, expect, it, vi } from 'vitest'
import { buscarProjecao } from '../api.js'

describe('buscarProjecao', () => {
  it('chama GET /projecoes com ano e recorte', async () => {
    const fetcher = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({}) })
    await buscarProjecao({ ano: 2075, recorte: 'chefe_60_mais' }, { fetcher, base: 'http://api' })
    expect(fetcher.mock.calls[0][0]).toBe('http://api/projecoes?ano=2075&recorte=chefe_60_mais')
  })
})
