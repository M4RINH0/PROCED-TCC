import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import Panorama from '../../src/pages/Panorama.jsx'
import { PADRAO_SIMULACAO } from '../../src/utils/simulacao.js'

/* Valores reais da API para o Brasil em 2050, todos os domicílios, controles no padrão (intensidade 0,6 e k 1):
   taxas 78,5, arranjos fixos 74,9, contrafactual 71,5; efeito da idade 3,4 e dos arranjos 3,6 */
const celulas = (baixa) => [
  { faixa: '80+', arranjo: 'Unipessoal (Mononuclear)', domicilios_amostra: baixa ? 3 : 592, baixa_confiabilidade: baixa },
  { faixa: '80+', arranjo: 'Casal ou Dupla', domicilios_amostra: 754, baixa_confiabilidade: false },
]
const vazio = (id) => ({ id, valor: null, consumo_por_pessoa_kwh: null, consumo_total_calibrado_kwh_mes: null, variacao_kwh: null, variacao_pct: null })

const serie = (recorte, { baixa = false, localidade = 'Brasil', simulacao = false } = {}) => ({
  recorte,
  unidade: 'kWh/mes/pessoa',
  fonte: 'POF 2002 a 2003, 2008 a 2009 e 2017 a 2018 e Projeções da População (IBGE)',
  dados_ilustrativos: false,
  localidade,
  domicilios_amostra: 52102,
  celulas: celulas(baixa),
  baixa_confiabilidade: baixa,
  intensidade: 0.6,
  k: 1,
  simulacao,
  pontos: Array.from({ length: 45 }, (_, i) => {
    const ano = 2026 + i
    const taxas = recorte === 'todos_domicilios' ? 78.5 : 88.7
    return {
      ano,
      cenarios: [
        { id: 'taxas', valor: taxas, consumo_por_pessoa_kwh: 67.4, consumo_total_calibrado_kwh_mes: 14565989146, participacao_consumo_pct: recorte === 'todos_domicilios' ? 100 : 43.6, variacao_kwh: 7.0, variacao_pct: 9.8 },
        { id: 'taxas_arranjos_fixos', valor: 74.9, consumo_por_pessoa_kwh: 63.9, consumo_total_calibrado_kwh_mes: 13790804959, participacao_consumo_pct: recorte === 'todos_domicilios' ? 100 : 33.3, variacao_kwh: 3.4, variacao_pct: 4.8 },
        vazio('ml_rf'),
        vazio('ml_gb'),
        { id: 'contrafactual', valor: 71.5, consumo_por_pessoa_kwh: 61.0, consumo_total_calibrado_kwh_mes: 13228815250, participacao_consumo_pct: recorte === 'todos_domicilios' ? 100 : 19.3, variacao_kwh: 0, variacao_pct: 0 },
      ],
      participacao_60_mais_pct: 30,
      efeito_envelhecimento_kwh: 7.0,
      efeito_idade_kwh: 3.4,
      efeito_arranjos_kwh: 3.6,
      efeito_envelhecimento_total_kwh_mes: 1337173896,
      efeito_idade_total_kwh_mes: 561989709,
      efeito_arranjos_total_kwh_mes: 775184187,
      efeito_envelhecimento_participacao_pp: recorte === 'todos_domicilios' ? 0 : 24.3,
      efeito_idade_participacao_pp: recorte === 'todos_domicilios' ? 0 : 13.9,
      efeito_arranjos_participacao_pp: recorte === 'todos_domicilios' ? 0 : 10.4,
    }
  }),
})

const buscarOk = (opcoes) => vi.fn(({ recorte }) => Promise.resolve(serie(recorte, opcoes)))
const simulacaoCom = (valores, extra = {}) => ({
  valores,
  aplicados: valores,
  ativa: valores.k !== 1 || valores.intensidade !== 0.6,
  aoMudar: vi.fn(),
  restaurar: vi.fn(),
  ...extra,
})

describe('Panorama', () => {
  it('abre em todos os domicílios e mostra a leitura do ano', async () => {
    const buscar = buscarOk()
    render(<Panorama ano={2050} aoMudarAno={() => {}} buscar={buscar} />)
    expect(screen.getByLabelText('Carregando dados')).toBeInTheDocument()
    expect(await within(await screen.findByTestId('reg-taxas')).findByText('78,5 kWh')).toBeInTheDocument()
    expect(within(screen.getByTestId('reg-taxas_arranjos_fixos')).getByText('74,9 kWh')).toBeInTheDocument()
    expect(within(screen.getByTestId('reg-contrafactual')).getByText('71,5 kWh')).toBeInTheDocument()
    expect(buscar).toHaveBeenCalledWith({ recorte: 'todos_domicilios', localidade: 'Brasil', intensidade: 0.6, k: 1 }, expect.anything())
    expect(screen.getByLabelText(/Grupo exibido/)).toHaveValue('todos_domicilios')
    expect(screen.getByText(/Amostra da POF: 52.102 domicílios no recorte/)).toBeInTheDocument()
  })

  it('explica que efeito cada recorte mostra', async () => {
    render(<Panorama ano={2050} aoMudarAno={() => {}} buscar={buscarOk()} />)
    expect(screen.getByTestId('recorte-explica')).toHaveTextContent('Mostra os dois efeitos')
    fireEvent.change(screen.getByLabelText(/Grupo exibido/), { target: { value: 'chefe_60_mais_todos' } })
    expect(screen.getByTestId('recorte-explica')).toHaveTextContent('principalmente o efeito dos arranjos')
    fireEvent.change(screen.getByLabelText(/Grupo exibido/), { target: { value: 'chefe_60_mais' } })
    expect(screen.getByTestId('recorte-explica')).toHaveTextContent('esconde os dois efeitos')
    expect(screen.getByTestId('recorte-explica')).toHaveTextContent('não sobe só porque o grupo cresce')
  })

  it('descreve o efeito do envelhecimento decomposto em idade e arranjos', async () => {
    render(<Panorama ano={2050} aoMudarAno={() => {}} buscar={buscarOk()} />)
    await screen.findByTestId('reg-taxas')
    const frase = screen.getByRole('heading', { level: 1 }).nextElementSibling
    expect(frase).toHaveTextContent('no cenário envelhecimento e arranjos, consumo por pessoa dos domicílios do recorte (Brasil) é de 78,5 kWh/mês por pessoa')
    expect(frase).toHaveTextContent('Em relação ao cenário sem mudanças desde 2026, o envelhecimento soma +7,0 kWh por pessoa: +3,4 da idade e +3,6 da mudança de arranjos')
  })

  it('desenha taxas, arranjos fixos e contrafactual e esconde as séries null em todos os anos', async () => {
    render(<Panorama ano={2050} aoMudarAno={() => {}} buscar={buscarOk()} />)
    await screen.findByTestId('linha-taxas')
    expect(screen.getByTestId('linha-taxas_arranjos_fixos')).toBeInTheDocument()
    expect(screen.getByTestId('linha-contrafactual')).toBeInTheDocument()
    for (const id of ['ml_rf', 'ml_gb']) {
      expect(screen.queryByTestId(`linha-${id}`)).not.toBeInTheDocument()
      expect(screen.queryByTestId(`reg-${id}`)).not.toBeInTheDocument()
    }
    const legenda = screen.getByRole('group', { name: 'Séries exibidas' })
    expect(within(legenda).getAllByRole('button').map((b) => b.textContent)).toEqual(['Envelhecimento e arranjos', 'Só o envelhecimento', 'Sem mudanças desde 2026'])
  })

  it('envia os controles de simulação aplicados e mostra o rótulo de simulação', async () => {
    const buscar = vi.fn(({ recorte }) => Promise.resolve(serie(recorte, { simulacao: true })))
    const valores = { k: 1.3, intensidade: 1.2 }
    render(<Panorama ano={2050} aoMudarAno={() => {}} buscar={buscar} simulacao={simulacaoCom(valores)} />)
    await screen.findByTestId('reg-taxas')
    expect(buscar).toHaveBeenCalledWith({ recorte: 'todos_domicilios', localidade: 'Brasil', intensidade: 1.2, k: 1.3 }, expect.anything())
    expect(screen.getByTestId('rotulo-simulacao')).toHaveTextContent('Simulação')
    expect(screen.getByText('Simulação.')).toBeInTheDocument()
  })

  it('consulta só com os valores aplicados, não com os que estão sendo ajustados', async () => {
    const buscar = buscarOk()
    const sim = simulacaoCom({ k: 1.4, intensidade: 0.6 }, { aplicados: PADRAO_SIMULACAO })
    render(<Panorama ano={2050} aoMudarAno={() => {}} buscar={buscar} simulacao={sim} />)
    await screen.findByTestId('reg-taxas')
    expect(buscar).toHaveBeenCalledTimes(1)
    expect(buscar).toHaveBeenCalledWith(expect.objectContaining({ k: 1, intensidade: 0.6 }), expect.anything())
  })

  it('avisa "Atualizando para" a nova localidade e esmaece os dados antigos, sem trocar o nome antes da resposta', async () => {
    let resolver
    const buscar = vi.fn(({ recorte, localidade }) =>
      localidade === 'Brasil' ? Promise.resolve(serie(recorte)) : new Promise((r) => (resolver = () => r(serie(recorte, { localidade }))))
    )
    const brasil = { valor: 'Brasil', nome: 'Brasil', nomeDe: (v) => (v === 'NE' ? 'Nordeste' : v), regioes: [], aoMudar: () => {} }
    const { rerender } = render(<Panorama ano={2050} aoMudarAno={() => {}} buscar={buscar} local={brasil} />)
    await screen.findByTestId('reg-taxas')
    rerender(<Panorama ano={2050} aoMudarAno={() => {}} buscar={buscar} local={{ ...brasil, valor: 'NE', nome: 'Nordeste' }} />)
    expect(await screen.findByTestId('atualizando')).toHaveTextContent('Atualizando para Nordeste…')
    expect(buscar).toHaveBeenLastCalledWith(expect.objectContaining({ localidade: 'NE' }), expect.anything())
    // enquanto a resposta não chega, a frase continua dizendo de onde são os números
    expect(screen.getByText(/dos domicílios do recorte \(Brasil\)/)).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /Consumo por pessoa/ }).closest('section')).toHaveClass('esmaecido')
    await act(async () => resolver())
    expect(screen.queryByTestId('atualizando')).not.toBeInTheDocument()
    expect(screen.getByText(/dos domicílios do recorte \(Nordeste\)/)).toBeInTheDocument()
  })

  it('avisa quando falta o valor do método das taxas no ano', async () => {
    const buscar = vi.fn(({ recorte }) => {
      const r = serie(recorte)
      r.pontos[24].cenarios[0].valor = null
      return Promise.resolve(r)
    })
    render(<Panorama ano={2050} aoMudarAno={() => {}} buscar={buscar} />)
    expect(await within(await screen.findByTestId('reg-taxas')).findByText('Sem dado neste ano')).toBeInTheDocument()
    expect(screen.getByText(/Sem dado do cenário envelhecimento e arranjos/)).toBeInTheDocument()
  })

  it('mostra o aviso de baixa confiabilidade quando a API marca a célula', async () => {
    render(<Panorama ano={2050} aoMudarAno={() => {}} buscar={buscarOk({ baixa: true })} />)
    const aviso = await screen.findByTestId('aviso-amostra')
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
    fireEvent.change(screen.getByLabelText(/Grupo exibido/), { target: { value: 'mononuclear_abaixo_60' } })
    // o recorte mononucleares abre na participação; no consumo por pessoa, o valor do recorte é 88,7
    await waitFor(() => expect(within(screen.getByTestId('reg-taxas')).getByText('43,6 %')).toBeInTheDocument())
    fireEvent.change(screen.getByLabelText('Indicador do gráfico'), { target: { value: 'tbc' } })
    expect(within(screen.getByTestId('reg-taxas')).getByText('88,7 kWh')).toBeInTheDocument()
    expect(buscar).toHaveBeenLastCalledWith(expect.objectContaining({ recorte: 'mononuclear_abaixo_60' }), expect.anything())
  })

  it('não deixa esconder a última série visível', async () => {
    const avisar = vi.fn()
    render(<Panorama ano={2050} aoMudarAno={() => {}} avisar={avisar} buscar={buscarOk()} />)
    await screen.findByTestId('linha-taxas')
    fireEvent.click(screen.getByRole('button', { name: 'Sem mudanças desde 2026' }))
    fireEvent.click(screen.getByRole('button', { name: 'Só o envelhecimento' }))
    fireEvent.click(screen.getByRole('button', { name: 'Envelhecimento e arranjos' }))
    expect(avisar).toHaveBeenCalledWith('Mantenha ao menos uma série visível')
    expect(screen.getByRole('button', { name: 'Envelhecimento e arranjos' })).toHaveAttribute('aria-pressed', 'true')
  })

  it('mostra o erro no contexto, preserva os parâmetros e permite tentar de novo', async () => {
    const buscar = vi
      .fn()
      .mockRejectedValueOnce(new Error('A API respondeu com o código 503'))
      .mockImplementation(({ recorte }) => Promise.resolve(serie(recorte)))
    render(<Panorama ano={2050} aoMudarAno={() => {}} buscar={buscar} />)
    const alerta = await screen.findByRole('alert')
    expect(alerta).toHaveTextContent('ano 2050, grupo Todos os domicílios')
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
})


describe('Panorama: indicador do gráfico', () => {
  it('todos os domicílios abre no consumo por pessoa, com a participação indisponível', async () => {
    render(<Panorama ano={2050} aoMudarAno={() => {}} buscar={buscarOk()} />)
    await screen.findByTestId('reg-taxas')
    const indicador = screen.getByLabelText('Indicador do gráfico')
    expect(indicador).toHaveValue('tbc')
    const participacao = [...indicador.options].find((o) => o.value === 'participacao')
    expect(participacao.disabled).toBe(true)
    expect(participacao.textContent).toContain('sempre 100%')
  })

  it('os outros recortes abrem na participação, e o gráfico e a leitura seguem o indicador', async () => {
    render(<Panorama ano={2050} aoMudarAno={() => {}} buscar={buscarOk()} />)
    await screen.findByTestId('reg-taxas')
    fireEvent.change(screen.getByLabelText(/Grupo exibido/), { target: { value: 'chefe_60_mais_todos' } })
    await waitFor(() => expect(within(screen.getByTestId('reg-taxas')).getByText('43,6 %')).toBeInTheDocument())
    expect(screen.getByLabelText('Indicador do gráfico')).toHaveValue('participacao')
    expect(screen.getByRole('heading', { name: /Participação no consumo residencial/ })).toBeInTheDocument()
    expect(screen.getByText('43,6% em 2070')).toBeInTheDocument()
    expect(screen.getByTestId('decomposicao')).toHaveTextContent('+13,9 pontos percentuais')
  })

  it('o consumo total aparece em bilhões de kWh/mês, com a decomposição na mesma unidade', async () => {
    render(<Panorama ano={2050} aoMudarAno={() => {}} buscar={buscarOk()} />)
    await screen.findByTestId('reg-taxas')
    fireEvent.change(screen.getByLabelText('Indicador do gráfico'), { target: { value: 'total' } })
    expect(within(screen.getByTestId('reg-taxas')).getByText('14,6 bi kWh')).toBeInTheDocument()
    expect(screen.getByTestId('decomposicao')).toHaveTextContent('Efeito do envelhecimento+1,3 bilhões de kWh/mês')
    expect(screen.getByText('14,6 em 2070')).toBeInTheDocument()
  })
})
