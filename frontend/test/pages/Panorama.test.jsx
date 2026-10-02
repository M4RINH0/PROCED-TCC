import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import Panorama from '../../src/pages/Panorama.jsx'

const serie = (recorte) => ({
  recorte,
  unidade: 'kWh/mes/pessoa',
  fonte: 'POF 2017 a 2018 e Projeções da População (IBGE)',
  dados_ilustrativos: false,
  localidade: 'Brasil',
  domicilios_amostra: 9120,
  pontos: Array.from({ length: 45 }, (_, i) => {
    const ano = 2026 + i
    const valor = recorte === 'chefe_60_mais' ? 94.3 : 89.1
    return {
      ano,
      cenarios: [
        { id: 'mod', valor: null, variacao_kwh: null, variacao_pct: null },
        { id: 'ibge', valor, variacao_kwh: valor === null ? null : 0, variacao_pct: valor === null ? null : 0 },
        { id: 'alt', valor: null, variacao_kwh: null, variacao_pct: null },
      ],
      participacao_60_mais_pct: 30,
      amplitude_kwh: null,
      modelo_menos_oficial_kwh: null,
    }
  }),
})

const buscarOk = () => vi.fn(({ recorte }) => Promise.resolve(serie(recorte)))

describe('Panorama', () => {
  it('carrega a série e mostra a leitura do ano recebido da linha do tempo', async () => {
    const buscar = buscarOk()
    render(<Panorama ano={2050} aoMudarAno={() => {}} buscar={buscar} />)
    expect(screen.getByLabelText('Carregando dados')).toBeInTheDocument()
    expect(await within(await screen.findByTestId('reg-ibge')).findByText('94,3 kWh/mês')).toBeInTheDocument()
    expect(buscar).toHaveBeenCalledWith({ recorte: 'chefe_60_mais', localidade: 'Brasil' }, expect.anything())
    expect(screen.getByText(/Amostra da POF: 9.120 domicílios no recorte/)).toBeInTheDocument()
    expect(screen.getByText(/Fonte: POF 2017 a 2018/)).toBeInTheDocument()
    expect(screen.getByText(/a projeção oficial é de/)).toBeInTheDocument()
  })

  it('avisa quando falta o dado oficial do ano', async () => {
    const buscar = vi.fn(({ recorte }) => {
      const r = serie(recorte)
      r.pontos[24].cenarios[1].valor = null
      return Promise.resolve(r)
    })
    render(<Panorama ano={2050} aoMudarAno={() => {}} buscar={buscar} />)
    expect(await within(await screen.findByTestId('reg-ibge')).findByText('Sem dado neste ano')).toBeInTheDocument()
    expect(screen.getByText(/Sem dado da projeção oficial/)).toBeInTheDocument()
  })

  it('consulta de novo ao trocar o grupo', async () => {
    const buscar = buscarOk()
    render(<Panorama ano={2050} aoMudarAno={() => {}} buscar={buscar} />)
    await screen.findByTestId('linha-ibge')
    fireEvent.click(screen.getByRole('button', { name: 'Abaixo de 60' }))
    await waitFor(() => expect(within(screen.getByTestId('reg-ibge')).getByText('89,1 kWh/mês')).toBeInTheDocument())
    expect(buscar).toHaveBeenLastCalledWith({ recorte: 'mononuclear_abaixo_60', localidade: 'Brasil' }, expect.anything())
  })

  it('não deixa esconder a última série visível', async () => {
    const avisar = vi.fn()
    render(<Panorama ano={2050} aoMudarAno={() => {}} avisar={avisar} buscar={buscarOk()} />)
    await screen.findByTestId('linha-ibge')
    fireEvent.click(screen.getByRole('button', { name: 'Modelo' }))
    fireEvent.click(screen.getByRole('button', { name: 'Alternativo' }))
    fireEvent.click(screen.getByRole('button', { name: 'IBGE oficial' }))
    expect(avisar).toHaveBeenCalledWith('Mantenha ao menos uma série visível')
    expect(screen.getByRole('button', { name: 'IBGE oficial' })).toHaveAttribute('aria-pressed', 'true')
  })

  it('mostra o erro no contexto, preserva os parâmetros e permite tentar de novo', async () => {
    const buscar = vi
      .fn()
      .mockRejectedValueOnce(new Error('A API respondeu com o código 503'))
      .mockImplementation(({ recorte }) => Promise.resolve(serie(recorte)))
    render(<Panorama ano={2050} aoMudarAno={() => {}} buscar={buscar} />)
    const alerta = await screen.findByRole('alert')
    expect(alerta).toHaveTextContent('ano 2050, grupo Chefe 60+')
    fireEvent.click(screen.getByRole('button', { name: 'Tentar novamente' }))
    expect(await screen.findByTestId('linha-ibge')).toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('abre a gaveta de fontes', async () => {
    const abrirGaveta = vi.fn()
    render(<Panorama ano={2050} aoMudarAno={() => {}} abrirGaveta={abrirGaveta} buscar={buscarOk()} />)
    fireEvent.click(screen.getByRole('button', { name: 'Ver fontes' }))
    expect(abrirGaveta).toHaveBeenCalledWith('fontes')
  })

  it('consulta a localidade escolhida e mostra o nome dela', async () => {
    const buscar = buscarOk()
    const local = { valor: 'DF', nome: 'Distrito Federal', regioes: [], aoMudar: () => {} }
    render(<Panorama ano={2050} aoMudarAno={() => {}} buscar={buscar} local={local} />)
    await screen.findByTestId('linha-ibge')
    expect(buscar).toHaveBeenCalledWith({ recorte: 'chefe_60_mais', localidade: 'DF' }, expect.anything())
    expect(screen.getByText(/nos domicílios do recorte \(Distrito Federal\)/)).toBeInTheDocument()
  })
})
