import { describe, expect, it } from 'vitest'
import { melhorGrade } from '../../src/utils/grade.js'

describe('melhorGrade', () => {
  it('num painel largo, usa mais colunas que linhas (conta feita à mão)', () => {
    // 673 x 312: espaço = 312 x 0,012 = 3,744; 15 colunas e 7 linhas:
    // largura (673 - 14 x 3,744) / 15 = 41,372; altura (312 - 6 x 3,744) / 7 = 41,362; vale a menor
    const g = melhorGrade(673, 312)
    expect([g.colunas, g.linhas]).toEqual([15, 7])
    expect(g.gap).toBeCloseTo(3.744, 3)
    expect(g.celula).toBeCloseTo(41.362, 3)
  })

  it('num painel quase quadrado, volta à grade de 10 por 10', () => {
    // 362 x 320: espaço 3,84; altura (320 - 9 x 3,84) / 10 = 28,544
    const g = melhorGrade(362, 320)
    expect([g.colunas, g.linhas]).toEqual([10, 10])
    expect(g.celula).toBeCloseTo(28.544, 3)
  })

  it('num painel muito baixo, para no limite de 25 colunas e o espaço mínimo de 3 px', () => {
    // 2000 x 100: 100 x 0,012 = 1,2, então espaço 3; altura (100 - 3 x 3) / 4 = 22,75
    const g = melhorGrade(2000, 100)
    expect([g.colunas, g.linhas, g.gap]).toEqual([25, 4, 3])
    expect(g.celula).toBeCloseTo(22.75, 3)
  })

  it('sempre cabe as 100 casas, sem sobrar uma linha inteira vazia', () => {
    for (const [w, h] of [[300, 900], [520, 420], [919, 587], [1200, 320], [330, 320]]) {
      const g = melhorGrade(w, h)
      expect(g.colunas * g.linhas).toBeGreaterThanOrEqual(100)
      expect(g.colunas * (g.linhas - 1)).toBeLessThan(100)
      expect(g.celula * g.colunas + g.gap * (g.colunas - 1)).toBeLessThanOrEqual(w + 1e-9)
      expect(g.celula * g.linhas + g.gap * (g.linhas - 1)).toBeLessThanOrEqual(h + 1e-9)
    }
  })
})
