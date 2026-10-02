import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { buscarArranjos } from '../api.js'
import DomiciliosTela from '../components/DomiciliosTela.jsx'

const resposta = (grupo) => ({
  grupo,
  unidade: 'kWh/mes/pessoa',
  fonte: 'POF 2017 a 2018 (IBGE)',
  arranjos: [
    { arranjo: 'Unipessoal (Mononuclear)', mononuclear: true, chefe_60_mais: true, domicilios_amostra: 3415, consumo_per_capita_kwh: 115.7, consumo_total_kwh: 115.7, gasto_rs: 78.97 },
    { arranjo: 'Multipessoal (3+)', mononuclear: false, chefe_60_mais: false, domicilios_amostra: 25216, consumo_per_capita_kwh: 50.4, consumo_total_kwh: 190.8, gasto_rs: 133.5 },
  ],
})

describe('buscarArranjos', () => {
  it('chama GET /arranjos com o grupo', async () => {
    const fetcher = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({}) })
    await buscarArranjos({ grupo: 'abaixo_60' }, { fetcher, base: 'http://api' })
    expect(fetcher.mock.calls[0][0]).toBe('http://api/arranjos?grupo=abaixo_60')
  })
})

describe('DomiciliosTela', () => {
  it('lista os arranjos em formato brasileiro e destaca o recorte', async () => {
    render(<DomiciliosTela buscar={vi.fn(({ grupo }) => Promise.resolve(resposta(grupo)))} />)
    // no unipessoal o consumo por pessoa e o do domicílio são iguais: 115,7 aparece duas vezes na linha
    const [celula] = await screen.findAllByText('115,7')
    expect(celula.closest('tr')).toHaveClass('in')
    expect(screen.getByText('25.216')).toBeInTheDocument()
    expect(screen.getByText('50,4').closest('tr')).not.toHaveClass('in')
    expect(screen.getAllByText('mononuclear')).toHaveLength(1)
    expect(screen.getByText(/Fonte: POF/)).toBeInTheDocument()
  })

  it('filtra pela idade do chefe consultando a API', async () => {
    const buscar = vi.fn(({ grupo }) => Promise.resolve(resposta(grupo)))
    render(<DomiciliosTela buscar={buscar} />)
    await screen.findAllByText('115,7')
    fireEvent.click(screen.getByRole('button', { name: 'Chefe 60+' }))
    await waitFor(() => expect(buscar).toHaveBeenLastCalledWith({ grupo: 'chefe_60_mais' }, expect.anything()))
  })

  it('mostra o erro com o filtro preservado', async () => {
    render(<DomiciliosTela buscar={vi.fn().mockRejectedValue(new Error('A API respondeu com o código 503'))} />)
    expect(await screen.findByRole('alert')).toHaveTextContent('idade do chefe Todos')
  })

  it('avisa quando o filtro não tem dados', async () => {
    render(<DomiciliosTela buscar={() => Promise.resolve({ ...resposta('todos'), arranjos: [] })} />)
    expect(await screen.findByText('sem dado para este filtro')).toBeInTheDocument()
  })
})
