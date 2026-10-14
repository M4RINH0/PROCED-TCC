import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import GraficoSerie, { dominioY, marcasY } from '../../src/components/GraficoSerie.jsx'

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
const todas = { taxas: true, ml_rf: true, ml_gb: true, contrafactual: true }

describe('dominioY', () => {
  it('dá folga de 6 kWh e arredonda para múltiplos de 20, como o protótipo', () => {
    // mínimo 97,9 - 6 = 91,9 -> 80; máximo 98,1 + 6 = 104,1 -> 120
    expect(dominioY([taxas])).toEqual([80, 120])
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
    expect(screen.getByText('Taxas')).toBeInTheDocument()
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
    expect(screen.getByText('Contrafactual')).toBeInTheDocument()
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
