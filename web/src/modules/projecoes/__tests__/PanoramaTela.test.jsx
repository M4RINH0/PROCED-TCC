import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import PanoramaTela from '../components/PanoramaTela.jsx'

const resposta = (ano, recorte) => ({
  ano,
  recorte,
  unidade: 'kWh/mes/pessoa',
  cenarios: [
    { id: 'mod', valor: 230.3 },
    { id: 'ibge', valor: ano > 2060 ? null : 200 },
    { id: 'alt', valor: 262.3 },
  ],
  dados_ilustrativos: true,
})

describe('PanoramaTela', () => {
  it('mostra o carregamento e depois a leitura do ano', async () => {
    const buscar = vi.fn(({ ano, recorte }) => Promise.resolve(resposta(ano, recorte)))
    render(<PanoramaTela buscar={buscar} />)
    expect(screen.getByLabelText('Carregando dados')).toBeInTheDocument()
    expect(await screen.findByText(/230,3/)).toBeInTheDocument()
    expect(buscar).toHaveBeenCalledWith({ ano: 2075, recorte: 'chefe_60_mais' }, expect.anything())
    expect(screen.getByText(/Valores ilustrativos/)).toBeInTheDocument()
    expect(screen.getAllByText('Sem projeção oficial após 2060').length).toBeGreaterThan(0)
  })

  it('consulta de novo ao trocar o ano e o grupo', async () => {
    const buscar = vi.fn(({ ano, recorte }) => Promise.resolve(resposta(ano, recorte)))
    render(<PanoramaTela buscar={buscar} />)
    await screen.findByText(/230,3/)
    fireEvent.change(screen.getByLabelText(/Ano/), { target: { value: '2040' } })
    fireEvent.click(screen.getByRole('button', { name: 'Abaixo de 60' }))
    await waitFor(() =>
      expect(buscar).toHaveBeenLastCalledWith({ ano: 2040, recorte: 'mononuclear_abaixo_60' }, expect.anything()),
    )
    expect(screen.getByRole('button', { name: 'Abaixo de 60' })).toHaveAttribute('aria-pressed', 'true')
  })

  it('mostra o erro no contexto, preserva os parâmetros e permite tentar de novo', async () => {
    const buscar = vi
      .fn()
      .mockRejectedValueOnce(new Error('Não foi possível conectar à API'))
      .mockImplementation(({ ano, recorte }) => Promise.resolve(resposta(ano, recorte)))
    render(<PanoramaTela buscar={buscar} />)
    const alerta = await screen.findByRole('alert')
    expect(alerta).toHaveTextContent('Não foi possível carregar a projeção')
    expect(alerta).toHaveTextContent('ano 2075')
    expect(alerta).toHaveTextContent('grupo Chefe 60+')
    fireEvent.click(screen.getByRole('button', { name: 'Tentar novamente' }))
    expect(await screen.findByText(/230,3/)).toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
})
