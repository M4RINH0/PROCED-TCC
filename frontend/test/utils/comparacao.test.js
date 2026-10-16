import { describe, expect, it } from 'vitest'
import {
  ATALHOS,
  GRUPOS,
  escalaY,
  estiloDoGrupo,
  formatarPct,
  formatarValor,
  fraseResumo,
  soAgregados,
} from '../../src/utils/comparacao.js'
import { compacto } from '../../src/utils/formato.js'

describe('grupos da comparação', () => {
  it('tem as seis células e os quatro agregados, com os ids da API', () => {
    expect(GRUPOS.map((g) => g.id)).toEqual(['uni_60', 'cas_60', 'mul_60', 'uni_59', 'cas_59', 'mul_59', 'mono_60', 'mono_59', 'todos_60', 'todos_59'])
    expect(GRUPOS.filter((g) => g.arranjo === null)).toHaveLength(4)
  })

  it('os atalhos pedidos existem e respeitam o limite de 2 a 6 grupos', () => {
    expect(ATALHOS[0]).toMatchObject({ rotulo: 'Arranjos com chefe 60+', grupos: ['uni_60', 'cas_60', 'mul_60'] })
    expect(ATALHOS.find((a) => a.grupos.join() === 'mul_60,mul_59').rotulo).toBe('60+ contra abaixo de 60 no multipessoal')
    for (const a of ATALHOS) expect(a.grupos.length).toBeGreaterThanOrEqual(2)
  })

  it('reconhece seleção só de agregados', () => {
    expect(soAgregados(['mono_60', 'todos_59'])).toBe(true)
    expect(soAgregados(['mono_60', 'uni_60'])).toBe(false)
    expect(soAgregados([])).toBe(false)
  })
})

describe('estiloDoGrupo', () => {
  it('cor pelo arranjo, traço pela idade e agregado neutro e mais grosso', () => {
    expect(estiloDoGrupo('cas_60')).toEqual({ cor: 'var(--g-casal_ou_dupla)', tracejado: undefined, espessura: 2.2 })
    expect(estiloDoGrupo('cas_59')).toEqual({ cor: 'var(--g-casal_ou_dupla)', tracejado: '7 5', espessura: 2.2 })
    expect(estiloDoGrupo('todos_60')).toEqual({ cor: 'var(--g-agregado)', tracejado: undefined, espessura: 3.6 })
    expect(estiloDoGrupo('mono_59').tracejado).toBe('7 5')
  })

  it('nunca usa as cores de cenário (verde-petróleo e laranja)', () => {
    for (const g of GRUPOS) expect(estiloDoGrupo(g.id).cor).not.toMatch(/teal|orange/)
  })

  it('cada célula tem uma combinação única de cor e traço', () => {
    const combinacoes = GRUPOS.map((g) => estiloDoGrupo(g.id)).map((e) => `${e.cor}|${e.tracejado}|${e.espessura}`)
    expect(new Set(combinacoes.slice(0, 6)).size).toBe(6)
  })
})

describe('escalaY', () => {
  it('marcas redondas cobrindo o intervalo (índice de 98 a 267: passo 50)', () => {
    // (267 - 98) / 5 = 33,8 -> passo 50; de 50 a 300
    expect(escalaY([98.2, 266.7, 100])).toEqual({ lo: 50, hi: 300, marcas: [50, 100, 150, 200, 250, 300] })
  })

  it('números grandes: de 8,3 a 27,2 milhões, passo 5 milhões', () => {
    const { marcas } = escalaY([8_277_013, 27_165_330])
    expect(marcas).toEqual([5e6, 10e6, 15e6, 20e6, 25e6, 30e6])
  })

  it('série reta ganha folga e lista vazia tem padrão', () => {
    const { lo, hi } = escalaY([100, 100])
    expect(lo).toBeLessThan(100)
    expect(hi).toBeGreaterThan(100)
    expect(escalaY([null])).toEqual({ lo: 0, hi: 1, marcas: [0, 1] })
  })
})

describe('frase e formatação', () => {
  const tabela = [
    { id: 'uni_60', rotulo: 'Unipessoal 60+', variacao_pct: 141.3, ordem: 2 },
    { id: 'cas_60', rotulo: 'Casal ou dupla 60+', variacao_pct: 166.7, ordem: 1 },
    { id: 'mul_60', rotulo: 'Multipessoal 60+', variacao_pct: -1.8, ordem: 3 },
  ]

  it('resume quem cresce mais contra quem cresce menos, com os números da API', () => {
    expect(fraseResumo(tabela, 'Envelhecimento e arranjos').texto).toBe(
      'De 2026 a 2070, no cenário envelhecimento e arranjos, o grupo casal ou dupla 60+ cresce 166,7%, contra queda de 1,8% do grupo multipessoal 60+.',
    )
  })

  it('sem dois grupos com variação, não há frase', () => {
    expect(fraseResumo([{ ...tabela[0], ordem: null, variacao_pct: null }, tabela[1]], 'X')).toBeNull()
  })

  it('formata no padrão brasileiro e escreve "sem dado"', () => {
    expect(formatarValor(5937636, 'domicilios')).toBe('5.937.636')
    expect(formatarValor(32.59, 'participacao')).toBe('32,59')
    expect(formatarValor(-154828, 'domicilios', { sinal: true })).toBe('−154.828')
    expect(formatarValor(null, 'domicilios')).toBe('sem dado')
    expect(formatarPct(166.66)).toBe('+166,7%')
    expect(formatarPct(null)).toBe('sem dado')
  })

  it('compacta números grandes nos eixos', () => {
    expect(compacto(27_165_330)).toBe('27,2 mi')
    expect(compacto(14_565_989_146)).toBe('14,6 bi')
    expect(compacto(15_000)).toBe('15,0 mil')
    expect(compacto(250)).toBe('250')
    expect(compacto(98.5)).toBe('98,5')
  })
})
