import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import GraficoSerie, { afastarRotulos, dominioY, marcasY } from '../../src/components/GraficoSerie.jsx'

/* Valores reais da API (Brasil, chefe 60+): taxas 97,9 em 2026 e 98,1 em 2070 */
const taxas = {
  id: 'taxas',
  pontos: [
    { ano: 2026, valor: 97.9 },
    { ano: 2070, valor: 98.1 },
  ],
}
const contrafactual = {
  id: 'contrafactual',
  pontos: [
    { ano: 2026, valor: 97.9 },
    { ano: 2070, valor: 97.9 },
  ],
}
const vazio = { id: 'ml_rf', pontos: [{ ano: 2026, valor: null }] }
const todas = { taxas: true, taxas_arranjos_fixos: true, ml_rf: true, ml_gb: true, contrafactual: true }

describe('dominioY', () => {
  it('dá folga de 1 kWh e arredonda para múltiplos de 10', () => {
    // mínimo 97,9 - 1 = 96,9 -> 90; máximo 98,1 + 1 = 99,1 -> 100
    expect(dominioY([taxas])).toEqual([90, 100])
  })

  it('a curva de todos os domicílios (71,5 a 82,7 kWh) fica entre 70 e 90', () => {
    const todos = { id: 'taxas', pontos: [{ ano: 2026, valor: 71.5 }, { ano: 2070, valor: 82.7 }] }
    expect(dominioY([todos])).toEqual([70, 90])
    // marcas a cada 5 kWh: (90 - 70) / 5 = 4 -> passo 5
    expect(marcasY([70, 90])).toEqual([70, 75, 80, 85, 90])
  })

  it('mantém ao menos 10 kWh de altura com uma série reta', () => {
    expect(dominioY([{ id: 'contrafactual', pontos: [{ ano: 2026, valor: 80 }, { ano: 2070, valor: 80 }] }])).toEqual([70, 90])
    expect(dominioY([{ id: 'x', pontos: [{ ano: 2026, valor: 75 }] }])).toEqual([70, 80])
  })
  it('usa um padrão quando não há valores', () => expect(dominioY([vazio])).toEqual([120, 280]))
})

describe('marcasY', () => {
  it('escolhe o passo pela quantidade de marcas', () => {
    // (120 - 80) / 5 = 8 -> passo 10
    expect(marcasY([80, 120])).toEqual([80, 90, 100, 110, 120])
  })
})

describe('GraficoSerie', () => {
  it('desenha só as séries com dados e rotula o fim direto na linha', () => {
    render(<GraficoSerie series={[taxas, vazio]} visiveis={todas} ano={2050} aoMudarAno={() => {}} />)
    expect(screen.getByTestId('linha-taxas')).toBeInTheDocument()
    expect(screen.getByTestId('linha-ml_rf').getAttribute('d')).toBe('')
    expect(screen.getByText('98,1 em 2070')).toBeInTheDocument()
    expect(screen.getByText('Envelhecimento e arranjos')).toBeInTheDocument()
  })

  it('marca o ano selecionado e não desenha fronteira depois de 2070', () => {
    render(<GraficoSerie series={[taxas]} visiveis={todas} ano={2050} aoMudarAno={() => {}} />)
    expect(screen.getByText('2050')).toBeInTheDocument()
    expect(screen.queryByText(/Sem projeção oficial/)).not.toBeInTheDocument()
  })

  it('desenha taxas e contrafactual com cor e traço próprios', () => {
    render(<GraficoSerie series={[taxas, contrafactual]} visiveis={todas} ano={2050} aoMudarAno={() => {}} />)
    expect(screen.getByTestId('linha-taxas')).toHaveClass('s-taxas')
    expect(screen.getByTestId('linha-contrafactual')).toHaveClass('s-contrafactual')
    expect(screen.getByText('Sem mudanças desde 2026')).toBeInTheDocument()
  })

  it('não desenha série escondida pela legenda', () => {
    render(<GraficoSerie series={[taxas]} visiveis={{ ...todas, taxas: false }} ano={2050} aoMudarAno={() => {}} />)
    expect(screen.queryByTestId('linha-taxas')).not.toBeInTheDocument()
  })

  it('muda o ano pelo teclado, com Shift andando 5 anos', () => {
    const aoMudarAno = vi.fn()
    render(<GraficoSerie series={[taxas]} visiveis={todas} ano={2050} aoMudarAno={aoMudarAno} />)
    const grafico = screen.getByLabelText(/Use as setas/)
    fireEvent.keyDown(grafico, { key: 'ArrowRight' })
    fireEvent.keyDown(grafico, { key: 'ArrowLeft', shiftKey: true })
    fireEvent.keyDown(grafico, { key: 'End' })
    expect(aoMudarAno.mock.calls.map((c) => c[0])).toEqual([2051, 2045, 2070])
  })
})


describe('dominioY por indicador', () => {
  it('consumo total em bilhões: folga de 0,1 e múltiplos de 1', () => {
    const total = { id: 'taxas', pontos: [{ ano: 2026, valor: 12.78 }, { ano: 2070, valor: 14.57 }] }
    expect(dominioY([total], { folga: 0.1, passo: 1 })).toEqual([12, 15])
  })
  it('participação: folga de 0,5 e múltiplos de 5', () => {
    const part = { id: 'taxas', pontos: [{ ano: 2026, valor: 21.3 }, { ano: 2070, valor: 33.8 }] }
    expect(dominioY([part], { folga: 0.5, passo: 5 })).toEqual([20, 35])
  })
})

describe('afastarRotulos', () => {
  it('não mexe em rótulos já afastados', () => {
    expect(afastarRotulos([{ id: 'a', y: 50 }, { id: 'b', y: 120 }], 30, 0, 300)).toEqual([{ id: 'a', y: 50 }, { id: 'b', y: 120 }])
  })

  it('empurra para baixo o rótulo que encostaria no de cima, mantendo a ordem de entrada', () => {
    // 100, 105 e 110 -> 100, 130 e 160
    const r = afastarRotulos([{ id: 'c', y: 110 }, { id: 'a', y: 100 }, { id: 'b', y: 105 }], 30, 0, 300)
    expect(r).toEqual([{ id: 'c', y: 160 }, { id: 'a', y: 100 }, { id: 'b', y: 130 }])
  })

  it('perto do fim do gráfico, devolve para cima', () => {
    // 290, 292 e 295 com base 300 -> 240, 270 e 300
    const r = afastarRotulos([{ id: 'a', y: 290 }, { id: 'b', y: 292 }, { id: 'c', y: 295 }], 30, 0, 300)
    expect(r.map((i) => i.y)).toEqual([240, 270, 300])
  })

  it('perto do topo, empurra para baixo', () => {
    const r = afastarRotulos([{ id: 'a', y: -5 }, { id: 'b', y: 0 }], 30, 10, 300)
    expect(r.map((i) => i.y)).toEqual([10, 40])
  })
})

describe('rótulos do fim das linhas', () => {
  it('três séries com valores quase iguais não se sobrepõem', () => {
    // valores reais do recorte chefe 60+ mononucleares em 2070: 96,4, 97,8 e 97,6
    const serie = (id, v) => ({ id, pontos: [{ ano: 2026, valor: 97.6 }, { ano: 2070, valor: v }] })
    const series = [serie('taxas', 96.4), serie('taxas_arranjos_fixos', 97.8), serie('contrafactual', 97.6)]
    render(<GraficoSerie series={series} visiveis={todas} ano={2050} aoMudarAno={() => {}} />)
    const ys = ['taxas', 'taxas_arranjos_fixos', 'contrafactual'].map((id) => Number(screen.getByTestId(`rotulo-${id}`).dataset.y)).sort((a, b) => a - b)
    expect(ys[1] - ys[0]).toBeGreaterThanOrEqual(30)
    expect(ys[2] - ys[1]).toBeGreaterThanOrEqual(30)
  })

  it('mostra o sufixo do indicador no valor', () => {
    const part = { id: 'taxas', pontos: [{ ano: 2026, valor: 21.3 }, { ano: 2070, valor: 33.8 }] }
    render(<GraficoSerie series={[part]} visiveis={todas} ano={2050} aoMudarAno={() => {}} eixo={{ folga: 0.5, passo: 5 }} sufixo="%" />)
    expect(screen.getByText('33,8% em 2070')).toBeInTheDocument()
  })
})
