import { describe, expect, it } from 'vitest'
import { SERIES, seriesComDado, valoresDoCenario } from '../../src/utils/series.js'

const ponto = (ano, valores) => ({ ano, cenarios: Object.entries(valores).map(([id, valor]) => ({ id, valor })) })
const pontos = [
  ponto(2026, { taxas: 97.9, ml_rf: null, ml_gb: null, contrafactual: 97.9 }),
  ponto(2027, { taxas: null, ml_rf: null, ml_gb: null, contrafactual: 97.9 }),
]

describe('SERIES', () => {
  it('tem os quatro cenários da API na ordem do contrato', () => {
    expect(SERIES.map((s) => s.id)).toEqual(['taxas', 'ml_rf', 'ml_gb', 'contrafactual'])
  })

  it('usa verde-petróleo para as taxas, laranja para o contrafactual e cobalto para o ML', () => {
    const cor = Object.fromEntries(SERIES.map((s) => [s.id, s.cor]))
    expect(cor).toEqual({ taxas: 'teal', ml_rf: 'cobalt', ml_gb: 'cobalt', contrafactual: 'orange' })
  })

  it('diferencia cada série também pelo traço e pelo rótulo, não só pela cor', () => {
    const chaves = SERIES.map((s) => `${s.cor}/${s.traco}`)
    expect(new Set(chaves).size).toBe(SERIES.length)
    expect(new Set(SERIES.map((s) => s.curto)).size).toBe(SERIES.length)
  })
})

describe('seriesComDado', () => {
  it('esconde as séries que são null em todos os anos', () => {
    expect(seriesComDado(pontos).map((s) => s.id)).toEqual(['taxas', 'contrafactual'])
  })

  it('mantém a série que tem valor em pelo menos um ano', () => {
    expect(seriesComDado([pontos[1]]).map((s) => s.id)).toEqual(['contrafactual'])
  })

  it('devolve lista vazia sem pontos', () => expect(seriesComDado([])).toEqual([]))
})

describe('valoresDoCenario', () => {
  it('reorganiza a resposta por ano, sem cálculo', () => {
    expect(valoresDoCenario(pontos, 'taxas')).toEqual([
      { ano: 2026, valor: 97.9 },
      { ano: 2027, valor: null },
    ])
  })
})
