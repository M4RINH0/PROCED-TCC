import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import LeituraAno from '../../src/components/LeituraAno.jsx'
import { SERIES } from '../../src/utils/series.js'

const comDado = SERIES.filter((s) => s.id === 'taxas' || s.id === 'contrafactual')
const todas = { taxas: true, ml_rf: true, ml_gb: true, contrafactual: true }
/* Valores reais da API para o Brasil em 2050 (chefe 60+) */
const ponto = (taxas, extra = {}) => ({
  ano: 2050,
  cenarios: [
    { id: 'taxas', valor: taxas, consumo_total_calibrado_kwh_mes: taxas === null ? null : 3527888853, variacao_kwh: taxas === null ? null : 0.1, variacao_pct: taxas === null ? null : 0.1 },
    { id: 'ml_rf', valor: null, variacao_kwh: null, variacao_pct: null },
    { id: 'ml_gb', valor: null, variacao_kwh: null, variacao_pct: null },
    { id: 'contrafactual', valor: 97.9, consumo_total_calibrado_kwh_mes: 2327910204, variacao_kwh: 0, variacao_pct: 0 },
  ],
  participacao_60_mais_pct: 25.37,
  efeito_envelhecimento_kwh: null,
  efeito_envelhecimento_total_kwh_mes: null,
  ...extra,
})

describe('LeituraAno', () => {
  it('mostra o valor e a variação desde 2026 em formato brasileiro', () => {
    render(<LeituraAno ponto={ponto(98.0)} ano={2050} series={comDado} visiveis={todas} />)
    const reg = screen.getByTestId('reg-taxas')
    expect(within(reg).getByText('98,0 kWh/mês')).toBeInTheDocument()
    expect(within(reg).getByText('+0,1 kWh desde 2026 (+0,1%)')).toBeInTheDocument()
    expect(screen.getByText('25,4%')).toBeInTheDocument()
    expect(screen.getByText('3.527,9 milhões')).toBeInTheDocument()
  })

  it('só mostra as séries recebidas, sem as que não têm dado', () => {
    render(<LeituraAno ponto={ponto(98.0)} ano={2050} series={comDado} visiveis={todas} />)
    expect(screen.getByTestId('reg-contrafactual')).toBeInTheDocument()
    expect(screen.queryByTestId('reg-ml_rf')).not.toBeInTheDocument()
    expect(screen.queryByTestId('reg-ml_gb')).not.toBeInTheDocument()
  })

  it('avisa a falta do valor do ano em vez de mostrar um traço', () => {
    render(<LeituraAno ponto={ponto(null, { participacao_60_mais_pct: null })} ano={2050} series={comDado} visiveis={todas} />)
    expect(within(screen.getByTestId('reg-taxas')).getByText('Sem dado neste ano')).toBeInTheDocument()
    expect(screen.getAllByText('sem dado', { selector: 'b' })).toHaveLength(4)
  })

  it('mostra o efeito do envelhecimento quando a API o envia', () => {
    render(
      <LeituraAno
        ponto={ponto(98.0, { efeito_envelhecimento_kwh: 0.1, efeito_envelhecimento_total_kwh_mes: 1199978649 })}
        ano={2050}
        series={comDado}
        visiveis={todas}
      />,
    )
    expect(screen.getByText('+0,1 kWh')).toBeInTheDocument()
    expect(screen.getByText('+1.200,0 milhões')).toBeInTheDocument()
  })

  it('usa o sinal de menos quando o efeito é negativo', () => {
    render(
      <LeituraAno
        ponto={ponto(98.0, { efeito_envelhecimento_kwh: -1.5, efeito_envelhecimento_total_kwh_mes: -2500000 })}
        ano={2050}
        series={comDado}
        visiveis={todas}
      />,
    )
    expect(screen.getByText('−1,5 kWh')).toBeInTheDocument()
    expect(screen.getByText('−2,5 milhões')).toBeInTheDocument()
  })

  it('esmaece a série escondida na legenda', () => {
    render(<LeituraAno ponto={ponto(98.0)} ano={2050} series={comDado} visiveis={{ ...todas, taxas: false }} />)
    expect(screen.getByTestId('reg-taxas')).toHaveStyle({ opacity: '0.4' })
  })
})
