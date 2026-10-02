import { describe, expect, it, vi } from 'vitest'
import { buscarSerie, valoresDoCenario } from '../api.js'

describe('buscarSerie', () => {
  it('chama GET /projecoes/serie com o recorte', async () => {
    const fetcher = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({}) })
    await buscarSerie({ recorte: 'chefe_60_mais' }, { fetcher, base: 'http://api' })
    expect(fetcher.mock.calls[0][0]).toBe('http://api/projecoes/serie?recorte=chefe_60_mais')
  })
})

describe('valoresDoCenario', () => {
  it('extrai o valor de um cenário em cada ano, mantendo os nulos', () => {
    const pontos = [
      { ano: 2070, cenarios: [{ id: 'ibge', valor: 94.6 }] },
      { ano: 2071, cenarios: [{ id: 'ibge', valor: null }] },
    ]
    expect(valoresDoCenario(pontos, 'ibge')).toEqual([
      { ano: 2070, valor: 94.6 },
      { ano: 2071, valor: null },
    ])
    expect(valoresDoCenario(pontos, 'mod')).toEqual([
      { ano: 2070, valor: null },
      { ano: 2071, valor: null },
    ])
  })
})
