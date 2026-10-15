import { describe, expect, it } from 'vitest'
import {
  INDICADORES,
  efeitoDoIndicador,
  indicadorDisponivel,
  indicadorPadrao,
  porId,
  serieDoIndicador,
  valorDoIndicador,
} from '../../src/utils/indicadores.js'

describe('indicadores do gráfico', () => {
  it('são três, na ordem do seletor', () => {
    expect(INDICADORES.map((i) => i.rotulo)).toEqual([
      'Consumo por pessoa (TBC)',
      'Consumo total do recorte',
      'Participação no consumo residencial',
    ])
  })

  it('todos os domicílios abre no consumo por pessoa; os outros recortes, na participação', () => {
    expect(indicadorPadrao('todos_domicilios')).toBe('tbc')
    for (const r of ['chefe_60_mais_todos', 'chefe_60_mais', 'mononuclear_abaixo_60']) expect(indicadorPadrao(r)).toBe('participacao')
  })

  it('a participação não está disponível em todos os domicílios (sempre 100%)', () => {
    expect(indicadorDisponivel('participacao', 'todos_domicilios')).toBe(false)
    expect(indicadorDisponivel('participacao', 'chefe_60_mais')).toBe(true)
    expect(indicadorDisponivel('total', 'todos_domicilios')).toBe(true)
  })

  it('lê o campo do indicador e só muda a escala de exibição', () => {
    const cenario = { valor: 78.5, consumo_total_calibrado_kwh_mes: 14565989146, participacao_consumo_pct: 43.6 }
    expect(valorDoIndicador(cenario, porId('tbc'))).toBe(78.5)
    expect(valorDoIndicador(cenario, porId('total'))).toBeCloseTo(14.565989146)
    expect(valorDoIndicador(cenario, porId('participacao'))).toBe(43.6)
    expect(valorDoIndicador({ valor: null }, porId('tbc'))).toBeNull()
    expect(valorDoIndicador(undefined, porId('tbc'))).toBeNull()
  })

  it('monta a série do cenário e lê os efeitos com o sufixo do indicador', () => {
    const pontos = [{ ano: 2026, cenarios: [{ id: 'taxas', participacao_consumo_pct: 19.3 }] }]
    expect(serieDoIndicador(pontos, 'taxas', porId('participacao'))).toEqual([{ ano: 2026, valor: 19.3 }])
    const ponto = { efeito_idade_kwh: 3.4, efeito_idade_total_kwh_mes: 561989709, efeito_idade_participacao_pp: 13.9 }
    expect(efeitoDoIndicador(ponto, 'idade', porId('tbc'))).toBe(3.4)
    expect(efeitoDoIndicador(ponto, 'idade', porId('total'))).toBeCloseTo(0.561989709)
    expect(efeitoDoIndicador(ponto, 'idade', porId('participacao'))).toBe(13.9)
    expect(efeitoDoIndicador(ponto, 'arranjos', porId('tbc'))).toBeNull()
  })

  it('porId cai no consumo por pessoa com id desconhecido', () => {
    expect(porId('x').id).toBe('tbc')
  })
})
