import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { buscarSimulacao } from '../../src/services/api.js'
import Simulador from '../../src/pages/Simulador.jsx'

/* Resposta real da API para 70 a 79, unipessoal, Brasil, 2050, método das taxas */
const resposta = (p, extra = {}) => ({
  ano: p.ano,
  faixa: '70 a 79',
  arranjo: p.arranjo,
  base: p.base,
  valor: 120.5,
  motivo_sem_valor: null,
  domicilios_amostra: 1218,
  baixa_confiabilidade: false,
  domicilios_projetados: 4041963,
  participacao_pct: 4.48,
  consumo_total_calibrado_kwh_mes: 415447972,
  por_faixa: [
    { faixa: '60 a 69', domicilios_amostra: 1605, baixa_confiabilidade: false, consumo_per_capita_kwh: 117.7 },
    { faixa: '70 a 79', domicilios_amostra: 1218, baixa_confiabilidade: false, consumo_per_capita_kwh: 120.5 },
  ],
  unidade: 'kWh/mes/pessoa',
  fonte: 'POF 2017 a 2018 e Projeções da População (IBGE), média ponderada pelo peso amostral',
  ...extra,
})
const buscarOk = () => vi.fn((p) => Promise.resolve(resposta(p)))

describe('buscarSimulacao', () => {
  it('envia todos os parâmetros, sem a taxa', async () => {
    const fetcher = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({}) })
    await buscarSimulacao({ ano: 2050, faixa: '70_79', arranjo: 'unipessoal', base: 'taxas' }, { fetcher, base: 'http://api' })
    expect(fetcher.mock.calls[0][0]).toBe('http://api/simulador?ano=2050&faixa=70_79&arranjo=unipessoal&base=taxas')
  })
})

describe('Simulador', () => {
  it('consulta com os parâmetros padrão e mostra o demonstrativo', async () => {
    const buscar = buscarOk()
    render(<Simulador buscar={buscar} />)
    expect(await screen.findByText('120,5 kWh por mês por pessoa')).toBeInTheDocument()
    expect(buscar).toHaveBeenCalledWith(
      { ano: 2070, faixa: '70_79', arranjo: 'unipessoal', base: 'taxas', localidade: 'Brasil' },
      expect.anything(),
    )
    expect(screen.getByText(/média ponderada de 1.218/)).toBeInTheDocument()
    expect(screen.getByText('4.041.963 domicílios')).toBeInTheDocument()
    expect(screen.getByText(/4,5% do total/)).toBeInTheDocument()
    expect(screen.getByText('415,4 milhões de kWh/mês')).toBeInTheDocument()
  })

  it('oferece só o método das taxas e o contrafactual como cenário', () => {
    render(<Simulador buscar={buscarOk()} />)
    const opcoes = [...screen.getByLabelText('Cenário').querySelectorAll('option')].map((o) => o.value)
    expect(opcoes).toEqual(['taxas', 'contrafactual'])
  })

  it('não tem campo de taxa de envelhecimento', () => {
    render(<Simulador buscar={buscarOk()} />)
    expect(screen.queryByLabelText(/taxa/i)).not.toBeInTheDocument()
  })

  it('consulta de novo a cada mudança de parâmetro', async () => {
    const buscar = buscarOk()
    render(<Simulador buscar={buscar} />)
    await screen.findByText('120,5 kWh por mês por pessoa')
    fireEvent.change(screen.getByLabelText('Arranjo domiciliar'), { target: { value: 'casal_ou_dupla' } })
    await waitFor(() => expect(buscar).toHaveBeenLastCalledWith(expect.objectContaining({ arranjo: 'casal_ou_dupla' }), expect.anything()))
    fireEvent.change(screen.getByLabelText('Cenário'), { target: { value: 'contrafactual' } })
    await waitFor(() => expect(buscar).toHaveBeenLastCalledWith(expect.objectContaining({ base: 'contrafactual' }), expect.anything()))
  })

  it('explica quando a combinação não tem valor', async () => {
    const buscar = vi.fn((p) =>
      Promise.resolve(
        resposta(p, {
          valor: null,
          motivo_sem_valor: 'Sem domicílios na amostra para esta combinação.',
          domicilios_projetados: null,
          participacao_pct: null,
          consumo_total_calibrado_kwh_mes: null,
        }),
      ),
    )
    render(<Simulador buscar={buscar} />)
    expect(await screen.findByText('Sem dados para esta combinação')).toBeInTheDocument()
    expect(screen.getByText(/Sem domicílios na amostra para esta combinação\./)).toBeInTheDocument()
  })

  it('mostra o aviso de baixa confiabilidade quando a API marca a célula', async () => {
    const buscar = vi.fn((p) => Promise.resolve(resposta(p, { domicilios_amostra: 4, baixa_confiabilidade: true })))
    render(<Simulador buscar={buscar} />)
    expect(await screen.findByTestId('aviso-amostra')).toHaveTextContent('Baixa confiabilidade')
  })

  it('não mostra o aviso sem a marcação da API', async () => {
    render(<Simulador buscar={buscarOk()} />)
    await screen.findByText('120,5 kWh por mês por pessoa')
    expect(screen.queryByTestId('aviso-amostra')).not.toBeInTheDocument()
  })

  it('mostra o erro e tenta de novo', async () => {
    const buscar = vi.fn().mockRejectedValueOnce(new Error('A API respondeu com o código 503')).mockImplementation((p) => Promise.resolve(resposta(p)))
    render(<Simulador buscar={buscar} />)
    expect(await screen.findByRole('alert')).toHaveTextContent('código 503')
    fireEvent.click(screen.getByRole('button', { name: 'Tentar novamente' }))
    expect(await screen.findByText('120,5 kWh por mês por pessoa')).toBeInTheDocument()
  })

  it('restaura os parâmetros padrão', async () => {
    render(<Simulador buscar={buscarOk()} />)
    fireEvent.change(screen.getByLabelText('Ano de referência'), { target: { value: '2040' } })
    fireEvent.click(screen.getByRole('button', { name: 'Restaurar parâmetros' }))
    expect(screen.getByLabelText('Ano de referência')).toHaveValue('2070')
  })
})
