import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import LeituraAno from '../../src/components/LeituraAno.jsx'
import { porId } from '../../src/utils/indicadores.js'
import { SERIES } from '../../src/utils/series.js'

const comDado = SERIES.filter((s) => ['taxas', 'taxas_arranjos_fixos', 'contrafactual'].includes(s.id))
const todas = { taxas: true, taxas_arranjos_fixos: true, ml_rf: true, ml_gb: true, contrafactual: true }

/* Valores reais da API, todos os domicílios, Brasil, 2050, controles no padrão */
const ponto = (taxas, extra = {}) => ({
  ano: 2050,
  cenarios: [
    {
      id: 'taxas',
      valor: taxas,
      consumo_total_calibrado_kwh_mes: taxas === null ? null : 14565989146,
      participacao_consumo_pct: taxas === null ? null : 100,
      variacao_kwh: taxas === null ? null : 7.0,
      variacao_pct: taxas === null ? null : 9.8,
    },
    { id: 'taxas_arranjos_fixos', valor: 74.9, consumo_total_calibrado_kwh_mes: 13790804959, participacao_consumo_pct: 100, variacao_kwh: 3.4, variacao_pct: 4.8 },
    { id: 'ml_rf', valor: null },
    { id: 'ml_gb', valor: null },
    { id: 'contrafactual', valor: 71.5, consumo_total_calibrado_kwh_mes: 13228815250, participacao_consumo_pct: 100, variacao_kwh: 0, variacao_pct: 0 },
  ],
  participacao_60_mais_pct: 25.37,
  efeito_envelhecimento_kwh: 7.0,
  efeito_idade_kwh: 3.4,
  efeito_arranjos_kwh: 3.6,
  efeito_envelhecimento_total_kwh_mes: 1337173896,
  efeito_idade_total_kwh_mes: 561989709,
  efeito_arranjos_total_kwh_mes: 775184187,
  efeito_envelhecimento_participacao_pp: -2.89,
  efeito_idade_participacao_pp: -2.89,
  efeito_arranjos_participacao_pp: 0,
  ...extra,
})

describe('LeituraAno', () => {
  it('no consumo por pessoa mostra o valor, a variação desde 2026 e os rótulos novos', () => {
    render(<LeituraAno ponto={ponto(78.5)} ano={2050} series={comDado} visiveis={todas} />)
    const reg = screen.getByTestId('reg-taxas')
    expect(within(reg).getByText('Envelhecimento e arranjos')).toBeInTheDocument()
    expect(within(reg).getByText('78,5 kWh')).toBeInTheDocument()
    expect(within(reg).getByText('+7,0 kWh desde 2026 (+9,8%)')).toBeInTheDocument()
    expect(within(screen.getByTestId('reg-taxas_arranjos_fixos')).getByText('Só o envelhecimento')).toBeInTheDocument()
    expect(within(screen.getByTestId('reg-contrafactual')).getByText('Sem mudanças desde 2026')).toBeInTheDocument()
    expect(screen.getByText('25,4%')).toBeInTheDocument()
  })

  it('a decomposição segue o indicador: consumo por pessoa', () => {
    render(<LeituraAno ponto={ponto(78.5)} ano={2050} series={comDado} visiveis={todas} indicador={porId('tbc')} />)
    const d = screen.getByTestId('decomposicao')
    expect(d).toHaveTextContent('Efeito do envelhecimento+7,0 kWh por pessoa')
    expect(d).toHaveTextContent('Efeito da idade+3,4 kWh por pessoa')
    expect(d).toHaveTextContent('Efeito dos arranjos+3,6 kWh por pessoa')
  })

  it('a decomposição segue o indicador: consumo total, em bilhões de kWh/mês', () => {
    render(<LeituraAno ponto={ponto(78.5)} ano={2050} series={comDado} visiveis={todas} indicador={porId('total')} />)
    // 14.565.989.146 kWh/mês = 14,6 bilhões; efeito 1.337.173.896 = 1,3 bilhão
    expect(within(screen.getByTestId('reg-taxas')).getByText('14,6 bi kWh')).toBeInTheDocument()
    expect(screen.getByTestId('decomposicao')).toHaveTextContent('Efeito do envelhecimento+1,3 bilhões de kWh/mês')
    expect(within(screen.getByTestId('reg-taxas')).queryByText(/desde 2026/)).not.toBeInTheDocument()
  })

  it('a decomposição segue o indicador: participação, em pontos percentuais', () => {
    render(<LeituraAno ponto={ponto(78.5)} ano={2050} series={comDado} visiveis={todas} indicador={porId('participacao')} />)
    expect(screen.getByTestId('decomposicao')).toHaveTextContent('Efeito do envelhecimento−2,9 pontos percentuais')
    expect(screen.getByText('Participação no consumo residencial')).toBeInTheDocument()
  })

  it('só mostra as séries recebidas, sem as que não têm dado', () => {
    render(<LeituraAno ponto={ponto(78.5)} ano={2050} series={comDado} visiveis={todas} />)
    expect(screen.queryByTestId('reg-ml_rf')).not.toBeInTheDocument()
    expect(screen.queryByTestId('reg-ml_gb')).not.toBeInTheDocument()
  })

  it('avisa a falta do valor do ano em vez de mostrar um traço', () => {
    const vazio = ponto(null, {
      participacao_60_mais_pct: null,
      efeito_envelhecimento_kwh: null,
      efeito_idade_kwh: null,
      efeito_arranjos_kwh: null,
    })
    render(<LeituraAno ponto={vazio} ano={2050} series={comDado} visiveis={todas} />)
    expect(within(screen.getByTestId('reg-taxas')).getByText('Sem dado neste ano')).toBeInTheDocument()
    expect(screen.getAllByText('sem dado', { selector: 'b' })).toHaveLength(4)
  })

  it('usa o sinal de menos quando o efeito é negativo', () => {
    render(<LeituraAno ponto={ponto(78.5, { efeito_envelhecimento_kwh: -1.5 })} ano={2050} series={comDado} visiveis={todas} />)
    expect(screen.getByTestId('decomposicao')).toHaveTextContent('−1,5 kWh por pessoa')
  })

  it('esmaece a série escondida na legenda', () => {
    render(<LeituraAno ponto={ponto(78.5)} ano={2050} series={comDado} visiveis={{ ...todas, taxas: false }} />)
    expect(screen.getByTestId('reg-taxas')).toHaveStyle({ opacity: '0.4' })
  })
})
