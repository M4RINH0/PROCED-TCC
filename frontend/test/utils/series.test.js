import { describe, expect, it } from 'vitest'
import { RECORTES, SERIES, seriesComDado, valoresDoCenario } from '../../src/utils/series.js'

const ponto = (ano, valores) => ({ ano, cenarios: Object.entries(valores).map(([id, valor]) => ({ id, valor })) })
const pontos = [
  ponto(2026, { taxas: 97.9, taxas_arranjos_fixos: null, contrafactual: 97.9 }),
  ponto(2027, { taxas: null, taxas_arranjos_fixos: null, contrafactual: 97.9 }),
]

describe('SERIES', () => {
  it('tem os três cenários da API na ordem do contrato, sem machine learning', () => {
    expect(SERIES.map((s) => s.id)).toEqual(['taxas', 'taxas_arranjos_fixos', 'contrafactual'])
  })

  it('usa verde-petróleo para as taxas e laranja para o contrafactual', () => {
    const cor = Object.fromEntries(SERIES.map((s) => [s.id, s.cor]))
    expect(cor).toEqual({ taxas: 'teal', taxas_arranjos_fixos: 'teal', contrafactual: 'orange' })
  })

  it('usa os rótulos simples na interface', () => {
    const rotulo = Object.fromEntries(SERIES.map((s) => [s.id, s.rotulo]))
    expect([rotulo.taxas, rotulo.taxas_arranjos_fixos, rotulo.contrafactual]).toEqual([
      'Envelhecimento e arranjos',
      'Só o envelhecimento',
      'Sem mudanças desde 2026',
    ])
  })

  it('taxas em traço cheio e arranjos fixos em verde-petróleo tracejado', () => {
    const traco = Object.fromEntries(SERIES.map((s) => [s.id, s.traco]))
    expect([traco.taxas, traco.taxas_arranjos_fixos]).toEqual(['solid', 'dashed'])
  })
})

describe('RECORTES', () => {
  it('abre em todos os domicílios e explica o efeito de cada recorte', () => {
    expect(RECORTES[0].id).toBe('todos_domicilios')
    expect(RECORTES.map((r) => r.id)).toEqual(['todos_domicilios', 'chefe_60_mais_todos', 'chefe_60_mais', 'mononuclear_abaixo_60'])
    expect(RECORTES[0].explica).toMatch(/idade/)
    expect(RECORTES[0].explica).toMatch(/arranjos/)
    expect(RECORTES[1].explica).toMatch(/principalmente o efeito dos arranjos/)
    expect(RECORTES[2].explica).toMatch(/esconde os dois efeitos/)
    for (const r of RECORTES.slice(1)) expect(r.explica).toMatch(/não sobe só porque o grupo cresce/)
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
