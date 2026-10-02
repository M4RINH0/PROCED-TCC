import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { buscarConsumoChefe, buscarPiramide } from '../api.js'
import EstruturaEtariaTela from '../components/EstruturaEtariaTela.jsx'
import Piramide from '../components/Piramide.jsx'

const FAIXAS = ['0 a 9', '10 a 19', '20 a 29', '30 a 39', '40 a 49', '50 a 59', '60 a 69', '70 a 79', '80+']
const piramide = (ano) => ({
  ano,
  participacao_60_mais_pct: ano === 2026 ? 17.07 : 37.79,
  fonte: 'Projeções da População (IBGE), Brasil',
  faixas: FAIXAS.map((faixa) => ({ faixa, homens_pct: 5, mulheres_pct: 6 })),
})
const consumo = (arranjo) => ({
  arranjo,
  unidade: 'kWh/mes/pessoa',
  fonte: 'POF 2017 a 2018 (IBGE)',
  faixas: [
    { faixa: 'até 29', domicilios_amostra: 1817, consumo_per_capita_kwh: 76.7 },
    { faixa: '80+', domicilios_amostra: 1346, consumo_per_capita_kwh: 95.6 },
    { faixa: '30 a 39', domicilios_amostra: 0, consumo_per_capita_kwh: null },
  ],
})

const props = () => ({
  buscarPir: vi.fn(({ ano }) => Promise.resolve(piramide(ano))),
  buscarConsumo: vi.fn(({ arranjo }) => Promise.resolve(consumo(arranjo))),
})

describe('api da estrutura etária', () => {
  it('monta as URLs dos dois endpoints', async () => {
    const fetcher = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({}) })
    await buscarPiramide({ ano: 2050 }, { fetcher, base: 'http://api' })
    await buscarConsumoChefe({ arranjo: 'todos' }, { fetcher, base: 'http://api' })
    expect(fetcher.mock.calls.map((c) => c[0])).toEqual([
      'http://api/estrutura-etaria/piramide?ano=2050',
      'http://api/estrutura-etaria/consumo-chefe?arranjo=todos',
    ])
  })
})

describe('Piramide', () => {
  it('desenha uma faixa por grupo de idade', () => {
    render(<Piramide faixas={piramide(2026).faixas} />)
    FAIXAS.forEach((f) => expect(screen.getByTestId(`faixa-${f}`)).toBeInTheDocument())
  })
})

describe('EstruturaEtariaTela', () => {
  it('mostra a participação de 60+ e a tabela de consumo por faixa', async () => {
    render(<EstruturaEtariaTela {...props()} />)
    expect(await screen.findByText('17,1%')).toBeInTheDocument()
    expect(await screen.findByText('95,6')).toBeInTheDocument()
    expect(screen.getByText('95,6').closest('tr')).toHaveClass('in')
    expect(screen.getByText('1.817')).toBeInTheDocument()
    expect(screen.getByText('sem dado')).toBeInTheDocument()
  })

  it('consulta a pirâmide ao mudar o ano e o consumo ao mudar o arranjo', async () => {
    const p = props()
    render(<EstruturaEtariaTela {...p} />)
    await screen.findByText('17,1%')
    fireEvent.change(screen.getByLabelText(/^Ano/), { target: { value: '2070' } })
    expect(await screen.findByText('37,8%')).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Arranjo domiciliar'), { target: { value: 'multipessoal' } })
    await waitFor(() => expect(p.buscarConsumo).toHaveBeenLastCalledWith({ arranjo: 'multipessoal' }, expect.anything()))
  })

  it('mostra o erro de cada painel no próprio painel', async () => {
    render(
      <EstruturaEtariaTela
        buscarPir={vi.fn().mockRejectedValue(new Error('A API respondeu com o código 503'))}
        buscarConsumo={vi.fn(({ arranjo }) => Promise.resolve(consumo(arranjo)))}
      />,
    )
    expect(await screen.findByRole('alert')).toHaveTextContent('ano 2026')
    expect(await screen.findByText('95,6')).toBeInTheDocument()
  })
})
