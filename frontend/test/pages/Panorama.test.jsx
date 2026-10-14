import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import Panorama from '../../src/pages/Panorama.jsx'

/* Valores reais da API para o Brasil em 2050 (chefe 60+): taxas 98,0, contrafactual 97,9 */
const celulas = (baixa) => [
  { faixa: '80+', arranjo: 'Unipessoal (Mononuclear)', domicilios_amostra: baixa ? 3 : 592, baixa_confiabilidade: baixa },
  { faixa: '80+', arranjo: 'Casal ou Dupla', domicilios_amostra: 754, baixa_confiabilidade: false },
]

const serie = (recorte, { baixa = false } = {}) => ({
  recorte,
  unidade: 'kWh/mes/pessoa',
  fonte: 'POF 2017 a 2018 e Projeções da População (IBGE)',
  dados_ilustrativos: false,
  localidade: 'Brasil',
  domicilios_amostra: 9120,
  celulas: celulas(baixa),
  baixa_confiabilidade: baixa,
  pontos: Array.from({ length: 45 }, (_, i) => {
    const ano = 2026 + i
    const taxas = recorte === 'chefe_60_mais' ? 98.0 : 88.7
    return {
      ano,
      cenarios: [
        { id: 'taxas', valor: taxas, consumo_por_pessoa_kwh: 93.0, consumo_total_calibrado_kwh_mes: 3527888853, variacao_kwh: 0.1, variacao_pct: 0.1 },
        { id: 'ml_rf', valor: null, consumo_por_pessoa_kwh: null, consumo_total_calibrado_kwh_mes: null, variacao_kwh: null, variacao_pct: null },
        { id: 'ml_gb', valor: null, consumo_por_pessoa_kwh: null, consumo_total_calibrado_kwh_mes: null, variacao_kwh: null, variacao_pct: null },
        { id: 'contrafactual', valor: 97.9, consumo_por_pessoa_kwh: 93.0, consumo_total_calibrado_kwh_mes: 2327910204, variacao_kwh: 0, variacao_pct: 0 },
      ],
      participacao_60_mais_pct: 30,
      efeito_envelhecimento_kwh: 0.1,
      efeito_envelhecimento_total_kwh_mes: 1199978649,
    }
  }),
})

const buscarOk = (opcoes) => vi.fn(({ recorte }) => Promise.resolve(serie(recorte, opcoes)))

describe('Panorama', () => {
  it('carrega a série e mostra a leitura do ano recebido da linha do tempo', async () => {
    const buscar = buscarOk()
    render(<Panorama ano={2050} aoMudarAno={() => {}} buscar={buscar} />)
    expect(screen.getByLabelText('Carregando dados')).toBeInTheDocument()
    expect(await within(await screen.findByTestId('reg-taxas')).findByText('98,0 kWh/mês')).toBeInTheDocument()
    expect(within(screen.getByTestId('reg-contrafactual')).getByText('97,9 kWh/mês')).toBeInTheDocument()
    expect(buscar).toHaveBeenCalledWith({ recorte: 'chefe_60_mais', localidade: 'Brasil' }, expect.anything())
    expect(screen.getByText(/Amostra da POF: 9.120 domicílios no recorte/)).toBeInTheDocument()
    expect(screen.getByText(/Fonte: POF 2017 a 2018 e Projeções da População \(IBGE\)/)).toBeInTheDocument()
  })

  it('descreve o efeito do envelhecimento, taxas menos contrafactual', async () => {
    render(<Panorama ano={2050} aoMudarAno={() => {}} buscar={buscarOk()} />)
    await screen.findByTestId('reg-taxas')
    expect(screen.getByText(/O efeito do envelhecimento/)).toBeInTheDocument()
    expect(screen.getByText('+0,1 kWh por pessoa')).toBeInTheDocument()
    expect(screen.getByText('+1.200,0 milhões de kWh/mês')).toBeInTheDocument()
  })

  it('esconde as séries que vêm null em todos os anos: sem linha, legenda nem leitura', async () => {
    render(<Panorama ano={2050} aoMudarAno={() => {}} buscar={buscarOk()} />)
    await screen.findByTestId('linha-taxas')
    expect(screen.getByTestId('linha-contrafactual')).toBeInTheDocument()
    for (const id of ['ml_rf', 'ml_gb']) {
      expect(screen.queryByTestId(`linha-${id}`)).not.toBeInTheDocument()
      expect(screen.queryByTestId(`reg-${id}`)).not.toBeInTheDocument()
    }
    const legenda = screen.getByRole('group', { name: 'Séries exibidas' })
    expect(within(legenda).getAllByRole('button').map((b) => b.textContent)).toEqual(['Taxas', 'Contrafactual'])
    expect(screen.queryByText(/Random Forest|Gradient Boosting/)).not.toBeInTheDocument()
  })

  it('não tem controle de taxa de envelhecimento', async () => {
    render(<Panorama ano={2050} aoMudarAno={() => {}} buscar={buscarOk()} />)
    await screen.findByTestId('reg-taxas')
    expect(screen.queryByLabelText(/taxa de envelhecimento/i)).not.toBeInTheDocument()
    expect(screen.queryByRole('slider')).not.toBeInTheDocument()
  })

  it('avisa quando falta o valor do método das taxas no ano', async () => {
    const buscar = vi.fn(({ recorte }) => {
      const r = serie(recorte)
      r.pontos[24].cenarios[0].valor = null
      return Promise.resolve(r)
    })
    render(<Panorama ano={2050} aoMudarAno={() => {}} buscar={buscar} />)
    expect(await within(await screen.findByTestId('reg-taxas')).findByText('Sem dado neste ano')).toBeInTheDocument()
    expect(screen.getByText(/Sem dado do método das taxas/)).toBeInTheDocument()
  })

  it('mostra o aviso de baixa confiabilidade quando a API marca a célula', async () => {
    render(<Panorama ano={2050} aoMudarAno={() => {}} buscar={buscarOk({ baixa: true })} />)
    const aviso = await screen.findByTestId('aviso-amostra')
    expect(aviso).toHaveTextContent('Baixa confiabilidade')
    expect(aviso).toHaveTextContent('80+, unipessoal (mononuclear): 3')
  })

  it('não mostra o aviso quando nenhuma célula está marcada', async () => {
    render(<Panorama ano={2050} aoMudarAno={() => {}} buscar={buscarOk()} />)
    await screen.findByTestId('reg-taxas')
    expect(screen.queryByTestId('aviso-amostra')).not.toBeInTheDocument()
  })

  it('consulta de novo ao trocar o grupo', async () => {
    const buscar = buscarOk()
    render(<Panorama ano={2050} aoMudarAno={() => {}} buscar={buscar} />)
    await screen.findByTestId('linha-taxas')
    fireEvent.click(screen.getByRole('button', { name: 'Abaixo de 60' }))
    await waitFor(() => expect(within(screen.getByTestId('reg-taxas')).getByText('88,7 kWh/mês')).toBeInTheDocument())
    expect(buscar).toHaveBeenLastCalledWith({ recorte: 'mononuclear_abaixo_60', localidade: 'Brasil' }, expect.anything())
  })

  it('não deixa esconder a última série visível', async () => {
    const avisar = vi.fn()
    render(<Panorama ano={2050} aoMudarAno={() => {}} avisar={avisar} buscar={buscarOk()} />)
    await screen.findByTestId('linha-taxas')
    fireEvent.click(screen.getByRole('button', { name: 'Contrafactual' }))
    fireEvent.click(screen.getByRole('button', { name: 'Taxas' }))
    expect(avisar).toHaveBeenCalledWith('Mantenha ao menos uma série visível')
    expect(screen.getByRole('button', { name: 'Taxas' })).toHaveAttribute('aria-pressed', 'true')
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
    expect(await screen.findByTestId('linha-taxas')).toBeInTheDocument()
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
    await screen.findByTestId('linha-taxas')
    expect(buscar).toHaveBeenCalledWith({ recorte: 'chefe_60_mais', localidade: 'DF' }, expect.anything())
    expect(screen.getByText(/os domicílios do recorte \(Distrito Federal\)/)).toBeInTheDocument()
  })
})
