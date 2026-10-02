import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import GraficoSerie, { dominioY, marcasY } from '../components/GraficoSerie.jsx'

const ibge = {
  id: 'ibge',
  pontos: [
    { ano: 2026, valor: 94.3 },
    { ano: 2070, valor: 94.6 },
    { ano: 2071, valor: null },
  ],
}
const vazio = { id: 'mod', pontos: [{ ano: 2026, valor: null }] }
const todas = { mod: true, ibge: true, alt: true }

describe('dominioY', () => {
  it('dá folga de 6 kWh e arredonda para múltiplos de 20, como o protótipo', () => {
    // mínimo 94,3 - 6 = 88,3 -> 80; máximo 94,6 + 6 = 100,6 -> 120
    expect(dominioY([ibge])).toEqual([80, 120])
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
    render(<GraficoSerie series={[ibge, vazio]} visiveis={todas} ano={2050} aoMudarAno={() => {}} />)
    expect(screen.getByTestId('linha-ibge')).toBeInTheDocument()
    expect(screen.getByTestId('linha-mod').getAttribute('d')).toBe('')
    expect(screen.getByText('94,6 em 2070')).toBeInTheDocument()
  })

  it('marca a fronteira de 2070 e o ano selecionado', () => {
    render(<GraficoSerie series={[ibge]} visiveis={todas} ano={2050} aoMudarAno={() => {}} />)
    expect(screen.getByText('Sem projeção oficial após 2070')).toBeInTheDocument()
    expect(screen.getByText('2050')).toBeInTheDocument()
  })

  it('não desenha série escondida pela legenda', () => {
    render(<GraficoSerie series={[ibge]} visiveis={{ ...todas, ibge: false }} ano={2050} aoMudarAno={() => {}} />)
    expect(screen.queryByTestId('linha-ibge')).not.toBeInTheDocument()
  })

  it('muda o ano pelo teclado, com Shift andando 5 anos', () => {
    const aoMudarAno = vi.fn()
    render(<GraficoSerie series={[ibge]} visiveis={todas} ano={2050} aoMudarAno={aoMudarAno} />)
    const grafico = screen.getByLabelText(/Use as setas/)
    fireEvent.keyDown(grafico, { key: 'ArrowRight' })
    fireEvent.keyDown(grafico, { key: 'ArrowLeft', shiftKey: true })
    fireEvent.keyDown(grafico, { key: 'End' })
    expect(aoMudarAno.mock.calls.map((c) => c[0])).toEqual([2051, 2045, 2075])
  })
})
