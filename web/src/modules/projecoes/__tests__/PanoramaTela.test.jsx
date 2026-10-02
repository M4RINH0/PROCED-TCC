import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import PanoramaTela from '../components/PanoramaTela.jsx'

const serie = (recorte) => ({
  recorte,
  unidade: 'kWh/mes/pessoa',
  fonte: 'POF 2017 a 2018 e Projeções da População (IBGE)',
  dados_ilustrativos: false,
  pontos: Array.from({ length: 50 }, (_, i) => {
    const ano = 2026 + i
    return {
      ano,
      cenarios: [
        { id: 'mod', valor: null },
        { id: 'ibge', valor: ano > 2070 ? null : recorte === 'chefe_60_mais' ? 94.3 : 89.1 },
        { id: 'alt', valor: null },
      ],
    }
  }),
})

describe('PanoramaTela', () => {
  it('carrega a série e mostra a leitura do ano selecionado', async () => {
    const buscar = vi.fn(({ recorte }) => Promise.resolve(serie(recorte)))
    render(<PanoramaTela buscar={buscar} />)
    expect(screen.getByLabelText('Carregando dados')).toBeInTheDocument()
    const ibge = await screen.findByTestId('reg-ibge')
    expect(within(ibge).getByText(/94,3/)).toBeInTheDocument()
    expect(buscar).toHaveBeenCalledWith({ recorte: 'chefe_60_mais' }, expect.anything())
    expect(screen.getByText(/Fonte: POF 2017 a 2018/)).toBeInTheDocument()
    expect(within(screen.getByTestId('reg-mod')).getByText('Cenário ainda não modelado')).toBeInTheDocument()
  })

  it('troca o ano sem nova consulta e mostra a ausência do oficial depois de 2070', async () => {
    const buscar = vi.fn(({ recorte }) => Promise.resolve(serie(recorte)))
    render(<PanoramaTela buscar={buscar} />)
    await screen.findByTestId('reg-ibge')
    fireEvent.change(screen.getByLabelText(/^Ano/), { target: { value: '2072' } })
    expect(within(screen.getByTestId('reg-ibge')).getByText('Sem projeção oficial após 2070')).toBeInTheDocument()
    expect(buscar).toHaveBeenCalledTimes(1)
  })

  it('consulta de novo ao trocar o grupo', async () => {
    const buscar = vi.fn(({ recorte }) => Promise.resolve(serie(recorte)))
    render(<PanoramaTela buscar={buscar} />)
    await screen.findByTestId('reg-ibge')
    fireEvent.click(screen.getByRole('button', { name: 'Abaixo de 60' }))
    await waitFor(() => expect(within(screen.getByTestId('reg-ibge')).getByText(/89,1/)).toBeInTheDocument())
    expect(buscar).toHaveBeenLastCalledWith({ recorte: 'mononuclear_abaixo_60' }, expect.anything())
  })

  it('mostra o erro no contexto, preserva os parâmetros e permite tentar de novo', async () => {
    const buscar = vi
      .fn()
      .mockRejectedValueOnce(new Error('A API respondeu com o código 503'))
      .mockImplementation(({ recorte }) => Promise.resolve(serie(recorte)))
    render(<PanoramaTela buscar={buscar} />)
    const alerta = await screen.findByRole('alert')
    expect(alerta).toHaveTextContent('ano 2070, grupo Chefe 60+')
    fireEvent.click(screen.getByRole('button', { name: 'Tentar novamente' }))
    expect(await screen.findByTestId('reg-ibge')).toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
})
