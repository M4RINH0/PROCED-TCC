import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import LeituraAno, { textoSemValor } from './LeituraAno.jsx'

const todas = { mod: true, ibge: true, alt: true }
const ponto = (ibge, extra = {}) => ({
  ano: 2050,
  cenarios: [
    { id: 'mod', valor: null, variacao_kwh: null, variacao_pct: null },
    { id: 'ibge', valor: ibge, variacao_kwh: ibge === null ? null : 0.1, variacao_pct: ibge === null ? null : 0.1 },
    { id: 'alt', valor: null, variacao_kwh: null, variacao_pct: null },
  ],
  participacao_60_mais_pct: 25.37,
  amplitude_kwh: null,
  modelo_menos_oficial_kwh: null,
  ...extra,
})

describe('LeituraAno', () => {
  it('mostra o valor e a variação desde 2026 em formato brasileiro', () => {
    render(<LeituraAno ponto={ponto(94.4)} ano={2050} modelados={['ibge']} visiveis={todas} />)
    const reg = screen.getByTestId('reg-ibge')
    expect(within(reg).getByText('94,4 kWh/mês')).toBeInTheDocument()
    expect(within(reg).getByText('+0,1 kWh desde 2026 (+0,1%)')).toBeInTheDocument()
    expect(screen.getByText('25,4%')).toBeInTheDocument()
  })

  it('avisa a falta do valor do ano em vez de mostrar um traço', () => {
    render(<LeituraAno ponto={ponto(null, { participacao_60_mais_pct: null })} ano={2050} modelados={['ibge']} visiveis={todas} />)
    expect(within(screen.getByTestId('reg-ibge')).getByText('Sem dado neste ano')).toBeInTheDocument()
  })

  it('diz que o cenário não foi modelado e mostra "sem dado" nos comparativos', () => {
    render(<LeituraAno ponto={ponto(94.4)} ano={2050} modelados={['ibge']} visiveis={todas} />)
    expect(within(screen.getByTestId('reg-mod')).getByText('Cenário ainda não modelado')).toBeInTheDocument()
    expect(screen.getAllByText('sem dado', { selector: 'b' })).toHaveLength(2)
  })

  it('mostra os comparativos quando a API os envia', () => {
    render(<LeituraAno ponto={ponto(94.4, { amplitude_kwh: 32, modelo_menos_oficial_kwh: -1.5 })} ano={2050} modelados={['ibge']} visiveis={todas} />)
    expect(screen.getByText('32,0 kWh')).toBeInTheDocument()
    expect(screen.getByText('−1,5 kWh')).toBeInTheDocument()
  })

  it('esmaece a série escondida na legenda', () => {
    render(<LeituraAno ponto={ponto(94.4)} ano={2050} modelados={['ibge']} visiveis={{ ...todas, ibge: false }} />)
    expect(screen.getByTestId('reg-ibge')).toHaveStyle({ opacity: '0.4' })
  })
})

describe('textoSemValor', () => {
  it('distingue cenário não modelado de ano sem valor', () => {
    expect(textoSemValor(false)).toBe('Cenário ainda não modelado')
    expect(textoSemValor(true)).toBe('Sem dado neste ano')
  })
})
