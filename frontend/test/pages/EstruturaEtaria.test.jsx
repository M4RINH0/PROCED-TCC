import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import Piramide from '../../src/components/Piramide.jsx'
import { buscarConsumoChefe, buscarPiramides } from '../../src/services/api.js'
import EstruturaEtaria from '../../src/pages/EstruturaEtaria.jsx'

const FAIXAS = ['0 a 9', '10 a 19', '20 a 29', '30 a 39', '40 a 49', '50 a 59', '60 a 69', '70 a 79', '80+']
const pir = (ano, pct) => ({ ano, participacao_60_mais_pct: pct, faixas: FAIXAS.map((faixa) => ({ faixa, homens_pct: 5, mulheres_pct: 6 })) })
const piramides = { fonte: 'Projeções da População (IBGE), Brasil', piramides: [pir(2026, 17.07), pir(2070, 37.79)] }
const consumo = (arranjo) => ({
  arranjo,
  unidade: 'kWh/mes/pessoa',
  fonte: 'POF 2017 a 2018 (IBGE), média ponderada pelo peso amostral',
  faixas: [
    { faixa: 'até 29', domicilios_amostra: 1814, baixa_confiabilidade: false, consumo_per_capita_kwh: 76.7 },
    { faixa: '30 a 39', domicilios_amostra: 0, baixa_confiabilidade: true, consumo_per_capita_kwh: null },
    { faixa: '80+', domicilios_amostra: 1346, baixa_confiabilidade: false, consumo_per_capita_kwh: 97.9 },
  ],
})
const props = () => ({
  buscarPir: vi.fn(() => Promise.resolve(piramides)),
  buscarConsumo: vi.fn(({ arranjo }) => Promise.resolve(consumo(arranjo))),
})

describe('api da estrutura etária', () => {
  it('monta as URLs dos dois endpoints', async () => {
    const fetcher = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({}) })
    await buscarPiramides({ localidade: 'Sul' }, { fetcher, base: 'http://api' })
    await buscarConsumoChefe({ arranjo: 'todos' }, { fetcher, base: 'http://api' })
    expect(fetcher.mock.calls.map((c) => c[0])).toEqual([
      'http://api/estrutura-etaria/piramides?localidade=Sul',
      'http://api/estrutura-etaria/consumo-chefe?arranjo=todos',
    ])
  })
})

describe('Piramide', () => {
  it('desenha uma faixa por grupo de idade, com o contorno de 2026', () => {
    const { container } = render(<Piramide faixas={pir(2070, 0).faixas} contorno={pir(2026, 0).faixas} />)
    FAIXAS.forEach((f) => expect(screen.getByTestId(`faixa-${f}`)).toBeInTheDocument())
    expect(container.querySelectorAll('rect.pout')).toHaveLength(18)
    expect(container.querySelectorAll('rect.p60')).toHaveLength(6)
  })
})

describe('EstruturaEtaria', () => {
  it('compara a participação de 60+ com 2026 e lista o consumo por faixa', async () => {
    render(<EstruturaEtaria ano={2070} {...props()} />)
    expect(await screen.findByText('37,8%')).toBeInTheDocument()
    expect(screen.getByText('17,1%')).toBeInTheDocument()
    expect(await screen.findByText('1.814')).toBeInTheDocument()
    // 97,9 aparece no gráfico e na tabela; a linha da tabela é do recorte
    const celula = screen.getAllByText('97,9').find((el) => el.tagName === 'TD')
    expect(celula.closest('tr')).toHaveClass('in')
    expect(screen.getByText('sem dado')).toBeInTheDocument()
  })

  it('marca a faixa de baixa confiabilidade e mostra o aviso', async () => {
    render(<EstruturaEtaria ano={2070} {...props()} />)
    const linha = (await screen.findByText('30 a 39', { selector: 'td' })).closest('tr')
    expect(linha).toHaveTextContent('baixa confiabilidade')
    expect(screen.getByText('80+', { selector: 'td' }).closest('tr')).not.toHaveTextContent('baixa confiabilidade')
    expect(screen.getByTestId('aviso-amostra')).toBeInTheDocument()
  })

  it('não mostra o aviso sem faixa marcada', async () => {
    const p = props()
    p.buscarConsumo = vi.fn(({ arranjo }) => {
      const r = consumo(arranjo)
      return Promise.resolve({ ...r, faixas: r.faixas.map((f) => ({ ...f, baixa_confiabilidade: false })) })
    })
    render(<EstruturaEtaria ano={2070} {...p} />)
    await screen.findByText('1.814')
    expect(screen.queryByTestId('aviso-amostra')).not.toBeInTheDocument()
  })

  it('avisa quando o ano não está na projeção', async () => {
    render(<EstruturaEtaria ano={2040} {...props()} />)
    expect(await screen.findByRole('heading', { name: 'Sem dado para 2040' })).toBeInTheDocument()
  })

  it('consulta o consumo de novo ao mudar o arranjo', async () => {
    const p = props()
    render(<EstruturaEtaria ano={2070} {...p} />)
    await screen.findByText('1.814')
    fireEvent.click(screen.getByRole('button', { name: 'Multipessoal' }))
    await waitFor(() => expect(p.buscarConsumo).toHaveBeenLastCalledWith({ arranjo: 'multipessoal', localidade: 'Brasil' }, expect.anything()))
    expect(p.buscarPir).toHaveBeenCalledTimes(1)
  })

  it('mostra o erro da pirâmide no próprio painel e mantém o consumo', async () => {
    render(
      <EstruturaEtaria
        ano={2050}
        buscarPir={vi.fn().mockRejectedValue(new Error('A API respondeu com o código 503'))}
        buscarConsumo={vi.fn(({ arranjo }) => Promise.resolve(consumo(arranjo)))}
      />,
    )
    expect(await screen.findByRole('alert')).toHaveTextContent('ano 2050')
    expect(await screen.findByText('1.814')).toBeInTheDocument()
  })
})

describe('EstruturaEtaria: controles de simulação', () => {
  it('a pirâmide recebe só k; a intensidade fica desabilitada com a explicação', async () => {
    const p = props()
    const valores = { k: 1.5, intensidade: 1.2 }
    render(<EstruturaEtaria ano={2070} {...p} simulacao={{ valores, aplicados: valores, ativa: true, aoMudar: vi.fn(), restaurar: vi.fn() }} />)
    await screen.findByText('37,8%')
    expect(p.buscarPir).toHaveBeenCalledWith({ localidade: 'Brasil', k: 1.5 }, expect.anything())
    expect(p.buscarConsumo).toHaveBeenCalledWith({ arranjo: 'mononucleares', localidade: 'Brasil' }, expect.anything())
    expect(screen.getByLabelText('Intensidade da mudança de arranjos')).toBeDisabled()
    expect(screen.getByText(/a mudança de arranjos não altera esta página/)).toBeInTheDocument()
  })
})

describe('EstruturaEtaria: revisão no navegador', () => {
  it('no erro, os dois rodapés citam as mesmas fontes do estado normal', async () => {
    const { FONTE_CONSUMO_CHEFE, FONTE_PIRAMIDE } = await import('../../src/utils/fontes.js')
    const falha = () => vi.fn().mockRejectedValue(new Error('A API respondeu com o código 503'))
    render(<EstruturaEtaria ano={2050} buscarPir={falha()} buscarConsumo={falha()} />)
    await screen.findAllByRole('alert')
    expect(screen.getByText(`Fonte: ${FONTE_PIRAMIDE}`, { exact: false })).toBeInTheDocument()
    expect(screen.getByText(`Fonte: ${FONTE_CONSUMO_CHEFE}`, { exact: false })).toBeInTheDocument()
  })

  it('filtros e simulação ficam na barra comum, como no Panorama', () => {
    render(<EstruturaEtaria ano={2050} {...props()} />)
    const barra = screen.getByRole('group', { name: 'Filtros de Estrutura etária' })
    expect(barra).toHaveClass('barra-filtros')
    expect(within(barra).getByLabelText('Região')).toBeInTheDocument()
    expect(within(barra).getByRole('button', { name: 'Parâmetros de simulação' })).toBeInTheDocument()
  })
})
