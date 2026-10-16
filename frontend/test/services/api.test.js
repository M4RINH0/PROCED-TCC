import { describe, expect, it, vi } from 'vitest'
import { valoresDoCenario } from '../../src/utils/series.js'
import { buscarSerie, exportarDados } from '../../src/services/api.js'

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
