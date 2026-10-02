import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { buscarSimulacao } from '../services/api.js'
import { lerTaxa } from '../utils/formato.js'
import Simulador from './Simulador.jsx'

const resposta = (p, extra = {}) => ({
  ano: p.ano,
  faixa: '70 a 79',
  arranjo: p.arranjo,
  base: p.base,
  taxa: p.taxa,
  valor: 115.7,
  motivo_sem_valor: null,
  domicilios_amostra: 1218,
  por_faixa: [
    { faixa: '60 a 69', domicilios_amostra: 1, consumo_per_capita_kwh: 114.3 },
    { faixa: '70 a 79', domicilios_amostra: 1218, consumo_per_capita_kwh: 115.7 },
  ],
  unidade: 'kWh/mes/pessoa',
  fonte: 'POF 2017 a 2018 (IBGE)',
  ...extra,
})
const buscarOk = () => vi.fn((p) => Promise.resolve(resposta(p)))

describe('lerTaxa', () => {
  it('aceita vírgula ou ponto entre 0 e 10', () => {
    expect([lerTaxa('1,7'), lerTaxa('0'), lerTaxa('10'), lerTaxa(' 2.25 ')]).toEqual([1.7, 0, 10, 2.25])
  })
  it('rejeita fora do domínio ou mal formatado', () => {
    expect([lerTaxa('10,5'), lerTaxa('-1'), lerTaxa('abc'), lerTaxa(''), lerTaxa('1,234')]).toEqual([null, null, null, null, null])
  })
})

describe('buscarSimulacao', () => {
  it('envia todos os parâmetros', async () => {
    const fetcher = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({}) })
    await buscarSimulacao({ ano: 2050, faixa: '70_79', arranjo: 'unipessoal', base: 'ibge', taxa: 1.7 }, { fetcher, base: 'http://api' })
    expect(fetcher.mock.calls[0][0]).toBe('http://api/simulador?ano=2050&faixa=70_79&arranjo=unipessoal&base=ibge&taxa=1.7')
  })
})

describe('Simulador', () => {
  it('consulta com os parâmetros padrão e mostra o demonstrativo', async () => {
    const buscar = buscarOk()
    render(<Simulador buscar={buscar} />)
    expect(await screen.findByText('115,7 kWh/mês por pessoa')).toBeInTheDocument()
    expect(buscar).toHaveBeenCalledWith({ ano: 2070, faixa: '70_79', arranjo: 'unipessoal', base: 'ibge', taxa: 1.7 }, expect.anything())
    expect(screen.getByText(/média de 1.218 domicílios/)).toBeInTheDocument()
  })

  it('consulta de novo a cada mudança de parâmetro', async () => {
    const buscar = buscarOk()
    render(<Simulador buscar={buscar} />)
    await screen.findByText('115,7 kWh/mês por pessoa')
    fireEvent.change(screen.getByLabelText('Arranjo domiciliar'), { target: { value: 'casal_ou_dupla' } })
    await waitFor(() => expect(buscar).toHaveBeenLastCalledWith(expect.objectContaining({ arranjo: 'casal_ou_dupla' }), expect.anything()))
  })

  it('bloqueia a consulta com taxa inválida e explica o erro', async () => {
    const buscar = buscarOk()
    render(<Simulador buscar={buscar} />)
    await screen.findByText('115,7 kWh/mês por pessoa')
    fireEvent.change(screen.getByLabelText('Taxa anual (%)'), { target: { value: '12' } })
    expect(screen.getByText('Consulta não realizada')).toBeInTheDocument()
    expect(screen.getByText('Informe um número entre 0 e 10, como 1,7.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Consultar cenário' })).toBeDisabled()
    expect(buscar).toHaveBeenCalledTimes(1)
  })

  it('explica quando a combinação não tem valor', async () => {
    const buscar = vi.fn((p) => Promise.resolve(resposta(p, { valor: null, motivo_sem_valor: 'Cenário ainda não modelado.' })))
    render(<Simulador buscar={buscar} />)
    expect(await screen.findByText('Sem dados para esta combinação')).toBeInTheDocument()
    expect(screen.getByText(/Cenário ainda não modelado\./)).toBeInTheDocument()
  })

  it('mostra o erro e tenta de novo', async () => {
    const buscar = vi.fn().mockRejectedValueOnce(new Error('A API respondeu com o código 503')).mockImplementation((p) => Promise.resolve(resposta(p)))
    render(<Simulador buscar={buscar} />)
    expect(await screen.findByRole('alert')).toHaveTextContent('código 503')
    fireEvent.click(screen.getByRole('button', { name: 'Tentar novamente' }))
    expect(await screen.findByText('115,7 kWh/mês por pessoa')).toBeInTheDocument()
  })

  it('restaura os parâmetros padrão', async () => {
    render(<Simulador buscar={buscarOk()} />)
    fireEvent.change(screen.getByLabelText('Ano de referência'), { target: { value: '2040' } })
    fireEvent.click(screen.getByRole('button', { name: 'Restaurar parâmetros' }))
    expect(screen.getByLabelText('Ano de referência')).toHaveValue('2070')
  })
})
