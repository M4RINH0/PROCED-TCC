import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import GraficoSerie, { dominioY, marcasY } from '../components/GraficoSerie.jsx'

const serieIbge = {
  id: 'ibge',
  pontos: [
    { ano: 2026, valor: 94.3 },
    { ano: 2070, valor: 94.6 },
    { ano: 2071, valor: null },
  ],
}

describe('dominioY', () => {
  it('começa no zero e deixa folga acima do máximo', () => {
    // 94,6 * 1,15 = 108,8 -> próximo múltiplo de 20 = 120
    expect(dominioY([serieIbge])).toEqual([0, 120])
  })
  it('usa um padrão quando não há valores', () => {
    expect(dominioY([{ id: 'mod', pontos: [{ ano: 2026, valor: null }] }])).toEqual([0, 100])
  })
})

describe('marcasY', () => {
  it('gera marcas de 20 em 20 até o máximo', () => expect(marcasY([0, 120])).toEqual([0, 20, 40, 60, 80, 100, 120]))
})

describe('GraficoSerie', () => {
  it('desenha só as séries com dados e rotula o fim direto na linha', () => {
    render(<GraficoSerie series={[serieIbge, { id: 'mod', pontos: [{ ano: 2026, valor: null }] }]} anoSelecionado={2050} />)
    expect(screen.getByTestId('linha-ibge')).toBeInTheDocument()
    expect(screen.queryByTestId('linha-mod')).not.toBeInTheDocument()
    expect(screen.getByText('94,6 em 2070')).toBeInTheDocument()
  })

  it('marca a fronteira de 2070', () => {
    render(<GraficoSerie series={[serieIbge]} anoSelecionado={2050} />)
    expect(screen.getByText('Sem projeção oficial após 2070')).toBeInTheDocument()
  })
})
