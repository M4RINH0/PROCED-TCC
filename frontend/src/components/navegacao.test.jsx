import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import Gaveta from './Gaveta.jsx'
import LinhaDoTempo, { posicao } from './LinhaDoTempo.jsx'
import MenuDemonstracao from './MenuDemonstracao.jsx'

afterEach(() => vi.unstubAllGlobals())

describe('LinhaDoTempo', () => {
  it('posiciona os anos de 2026 a 2075 de 0% a 100%', () => {
    expect([posicao(2026), posicao(2075)]).toEqual([0, 100])
    expect(posicao(2070)).toBeCloseTo(89.8, 1)
  })

  it('mostra o ano, marca 2070 e avisa a mudança do controle', () => {
    const aoMudarAno = vi.fn()
    render(<LinhaDoTempo ano={2050.4} aoMudarAno={aoMudarAno} />)
    expect(screen.getByText('2050', { selector: 'b' })).toBeInTheDocument()
    expect(screen.getByText('Hachura: sem projeção oficial após 2070')).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Ano da projeção'), { target: { value: '2060' } })
    expect(aoMudarAno).toHaveBeenCalledWith(2060)
  })

  it('com movimento reduzido, o play leva direto ao fim', () => {
    vi.stubGlobal('matchMedia', () => ({ matches: true }))
    const aoMudarAno = vi.fn()
    render(<LinhaDoTempo ano={2030} aoMudarAno={aoMudarAno} />)
    fireEvent.click(screen.getByRole('button', { name: 'Reproduzir os 50 anos' }))
    expect(aoMudarAno).toHaveBeenCalledWith(2075)
  })

  it('fica escondida no simulador', () => {
    const { container } = render(<LinhaDoTempo ano={2030} aoMudarAno={() => {}} oculta />)
    expect(container.querySelector('.dock')).toHaveClass('hide')
  })
})

describe('Gaveta', () => {
  const resposta = (dados) => vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve(dados) })

  it('lista as fontes vindas da API', async () => {
    vi.stubGlobal('fetch', resposta([{ id: 'pof', nome: 'Pesquisa de Orçamentos Familiares (IBGE)', periodo: '2017 a 2018', uso: 'Consumo' }]))
    render(<Gaveta tipo="fontes" ano={2050} aoFechar={() => {}} avisar={() => {}} />)
    expect(await screen.findByText('Pesquisa de Orçamentos Familiares (IBGE)')).toBeInTheDocument()
    expect(screen.getByRole('dialog')).toHaveAccessibleName('Fonte dos dados')
  })

  it('mostra a resposta real da API para o ano', async () => {
    const fetch = resposta({ ano: 2050, cenarios: [] })
    vi.stubGlobal('fetch', fetch)
    render(<Gaveta tipo="api" ano={2050.3} aoFechar={() => {}} avisar={() => {}} />)
    expect(await screen.findByText(/"ano": 2050/)).toBeInTheDocument()
    expect(fetch.mock.calls[0][0]).toContain('/projecoes?ano=2050&recorte=chefe_60_mais')
  })

  it('fecha com Esc e avisa que a exportação está pendente', () => {
    const aoFechar = vi.fn()
    const avisar = vi.fn()
    render(<Gaveta tipo="exportar" ano={2050} aoFechar={aoFechar} avisar={avisar} />)
    fireEvent.click(screen.getByRole('button', { name: 'Exportar' }))
    expect(avisar).toHaveBeenCalledWith('Exportação ainda não implementada (RF08)')
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(aoFechar).toHaveBeenCalledTimes(2)
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
