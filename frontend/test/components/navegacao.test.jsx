import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import Gaveta from '../../src/components/Gaveta.jsx'
import LinhaDoTempo, { posicao } from '../../src/components/LinhaDoTempo.jsx'
import MenuDemonstracao from '../../src/components/MenuDemonstracao.jsx'

afterEach(() => vi.unstubAllGlobals())

describe('LinhaDoTempo', () => {
  it('posiciona os anos de 2026 a 2070 de 0% a 100%', () => {
    expect([posicao(2026), posicao(2070)]).toEqual([0, 100])
    expect(posicao(2048)).toBe(50)
  })

  it('mostra o ano e avisa a mudança do controle', () => {
    const aoMudarAno = vi.fn()
    render(<LinhaDoTempo ano={2050.4} aoMudarAno={aoMudarAno} />)
    expect(screen.getByText('2050', { selector: 'b' })).toBeInTheDocument()
    expect(screen.queryByText(/Hachura/)).not.toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Ano da projeção'), { target: { value: '2060' } })
    expect(aoMudarAno).toHaveBeenCalledWith(2060)
  })

  it('com movimento reduzido, o play leva direto ao fim', () => {
    vi.stubGlobal('matchMedia', () => ({ matches: true }))
    const aoMudarAno = vi.fn()
    render(<LinhaDoTempo ano={2030} aoMudarAno={aoMudarAno} />)
    fireEvent.click(screen.getByRole('button', { name: 'Reproduzir os 45 anos' }))
    expect(aoMudarAno).toHaveBeenCalledWith(2070)
  })

  it('fica escondida no simulador', () => {
    const { container } = render(<LinhaDoTempo ano={2030} aoMudarAno={() => {}} oculta />)
    expect(container.querySelector('.dock')).toHaveClass('hide')
  })
})

describe('Gaveta', () => {
  const resposta = (dados) => vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve(dados) })

  it('lista as fontes, o critério de exclusão, a cobertura e as premissas vindas da API', async () => {
    vi.stubGlobal(
      'fetch',
      resposta({
        fontes: [{ id: 'pof', nome: 'Pesquisa de Orçamentos Familiares (IBGE)', periodo: '2017 a 2018', uso: 'Consumo' }],
        criterio_exclusao: 'Ficaram de fora, na extração, os domicílios sem declaração válida de consumo de energia (sem kWh).',
        cobertura_pct: 92.4,
        premissas: [
          { id: 'P2', texto: 'Taxa de chefia de 2018 constante.' },
          { id: 'P12', texto: 'Consumo total calibrado pela população do IBGE.' },
        ],
        premissas_url: 'https://github.com/M4RINH0/PROCED-TCC/blob/main/docs/premissas.md',
      }),
    )
    render(<Gaveta tipo="fontes" ano={2050} aoFechar={() => {}} avisar={() => {}} />)
    expect(await screen.findByText('Pesquisa de Orçamentos Familiares (IBGE)')).toBeInTheDocument()
    expect(screen.getByRole('dialog')).toHaveAccessibleName('Fonte dos dados')
    expect(screen.getByTestId('criterio')).toHaveTextContent('sem kWh')
    expect(screen.getByTestId('criterio')).toHaveTextContent('92,4%')
    expect(screen.getByText('P2')).toBeInTheDocument()
    expect(screen.getByText('Consumo total calibrado pela população do IBGE.')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /docs\/premissas.md/ })).toHaveAttribute('href', expect.stringContaining('docs/premissas.md'))
  })

  it('mostra a resposta real da API para o ano', async () => {
    const fetch = resposta({ ano: 2050, cenarios: [] })
    vi.stubGlobal('fetch', fetch)
    render(<Gaveta tipo="api" ano={2050.3} aoFechar={() => {}} avisar={() => {}} />)
    expect(await screen.findByText(/"ano": 2050/)).toBeInTheDocument()
    expect(fetch.mock.calls[0][0]).toContain('/projecoes?ano=2050&recorte=todos_domicilios&localidade=Brasil&intensidade=0.6&k=1')
  })

  it('exporta os dados em CSV ou XLSX com o escopo escolhido e fecha com Esc', async () => {
    const aoFechar = vi.fn()
    const avisar = vi.fn()
    const exportar = vi.fn().mockResolvedValue({ blob: new Blob(['a,b']), nomeArquivo: 'proced_SP_2050.csv' })
    render(
      <Gaveta
        tipo="exportar"
        ano={2050.4}
        localidade="SP"
        simulacao={{ intensidade: 1.1, k: 1.2 }}
        aoFechar={aoFechar}
        avisar={avisar}
        exportar={exportar}
      />,
    )
    fireEvent.click(screen.getByRole('button', { name: 'Exportar' }))
    expect(exportar).toHaveBeenCalledWith({
      formato: 'csv',
      escopo: 'ano',
      ano: 2050,
      localidade: 'SP',
      intensidade: 1.1,
      k: 1.2,
    })
    await screen.findByRole('button', { name: 'Exportar' })
    expect(avisar).toHaveBeenCalledWith('Dados exportados em CSV')
    expect(aoFechar).toHaveBeenCalledOnce()

    fireEvent.click(screen.getByLabelText(/XLSX/))
    fireEvent.click(screen.getByLabelText(/Série completa/))
    fireEvent.click(screen.getByRole('button', { name: 'Exportar' }))
    expect(exportar).toHaveBeenLastCalledWith({
      formato: 'xlsx',
      escopo: 'serie',
      ano: 2050,
      localidade: 'SP',
      intensidade: 1.1,
      k: 1.2,
    })
    await screen.findByRole('button', { name: 'Exportar' })
    expect(avisar).toHaveBeenLastCalledWith('Dados exportados em XLSX')

    fireEvent.keyDown(document, { key: 'Escape' })
    expect(aoFechar).toHaveBeenCalledTimes(3)
  })

  it('avisa quando a exportação falha', async () => {
    const avisar = vi.fn()
    const exportar = vi.fn().mockRejectedValue(new Error('falha'))
    render(<Gaveta tipo="exportar" ano={2050} aoFechar={() => {}} avisar={avisar} exportar={exportar} />)
    fireEvent.click(screen.getByRole('button', { name: 'Exportar' }))
    await screen.findByRole('button', { name: 'Exportar' })
    expect(avisar).toHaveBeenCalledWith('Não foi possível exportar os dados')
  })
})

describe('MenuDemonstracao', () => {
  it('abre o menu e alterna a falha simulada', () => {
    const aoAlternarFalha = vi.fn()
    const aoReverCarregamento = vi.fn()
    render(<MenuDemonstracao falha={false} aoAlternarFalha={aoAlternarFalha} aoReverCarregamento={aoReverCarregamento} />)
    fireEvent.click(screen.getByRole('button', { name: 'Demonstração' }))
    const chave = screen.getByRole('switch')
    expect(chave).toHaveAttribute('aria-checked', 'false')
    fireEvent.click(chave)
    expect(aoAlternarFalha).toHaveBeenCalledOnce()
    fireEvent.click(screen.getByRole('button', { name: /Rever carregamento/ }))
    expect(aoReverCarregamento).toHaveBeenCalledOnce()
    expect(screen.queryByRole('switch')).not.toBeInTheDocument()
  })
})

describe('Gaveta Fontes: como ler o Panorama', () => {
  it('explica cada linha e como os efeitos são calculados', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ fontes: [], criterio_exclusao: 'Sem kWh.', cobertura_pct: 92.4, premissas: [], premissas_url: 'x' }),
      }),
    )
    render(<Gaveta tipo="fontes" ano={2050} aoFechar={() => {}} avisar={() => {}} />)
    const guia = await screen.findByTestId('como-ler')
    for (const linha of ['Envelhecimento e arranjos', 'Só o envelhecimento', 'Sem mudanças desde 2026']) {
      expect(guia).toHaveTextContent(linha)
    }
    expect(guia).toHaveTextContent('Efeito da idade = só o envelhecimento menos sem mudanças desde 2026')
    expect(guia).toHaveTextContent('Efeito dos arranjos = envelhecimento e arranjos menos só o envelhecimento')
  })
})
