import { render, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import Gaveta from '../src/components/Gaveta.jsx'
import Panorama from '../src/pages/Panorama.jsx'
import Simulador, { BASES } from '../src/pages/Simulador.jsx'
import { rotuloDaSerie } from '../src/utils/series.js'

/* Os três cenários têm o mesmo nome em todas as páginas e na gaveta. Os rótulos esperados estão escritos
   por extenso de propósito: mudar um deles exige mudar este teste. */
const ESPERADOS = {
  taxas: 'Envelhecimento e arranjos',
  taxas_arranjos_fixos: 'Só o envelhecimento',
  contrafactual: 'Sem mudanças desde 2026',
}
const fontes = import.meta.glob('../src/**/*.{js,jsx}', { query: '?raw', import: 'default', eager: true })

const cenario = (id, valor) => ({ id, valor, consumo_por_pessoa_kwh: valor, consumo_total_calibrado_kwh_mes: valor && 1e9, participacao_consumo_pct: 100, variacao_kwh: 0, variacao_pct: 0 })
const serie = {
  recorte: 'todos_domicilios',
  unidade: 'kWh/mes/pessoa',
  fonte: 'POF 2002 a 2003, 2008 a 2009 e 2017 a 2018 e Projeções da População (IBGE)',
  localidade: 'Brasil',
  domicilios_amostra: 52102,
  celulas: [],
  baixa_confiabilidade: false,
  pontos: Array.from({ length: 45 }, (_, i) => ({
    ano: 2026 + i,
    cenarios: [cenario('taxas', 78.5), cenario('taxas_arranjos_fixos', 74.9), cenario('contrafactual', 71.5)],
  })),
}

afterEach(() => vi.unstubAllGlobals())

describe('rótulos dos cenários', () => {
  it('a fonte única (utils/series.js) tem os três nomes', () => {
    for (const [id, rotulo] of Object.entries(ESPERADOS)) expect(rotuloDaSerie(id)).toBe(rotulo)
  })

  it('o Simulador oferece os cenários com os nomes do Panorama', () => {
    render(<Simulador buscar={vi.fn(() => new Promise(() => {}))} />)
    const opcoes = [...screen.getByLabelText('Cenário').querySelectorAll('option')].map((o) => [o.value, o.textContent])
    expect(opcoes).toEqual(Object.entries(ESPERADOS))
    expect(BASES.map((b) => b.rotulo)).toEqual(Object.values(ESPERADOS))
  })

  it('o Panorama usa os mesmos nomes na legenda e na leitura do ano', async () => {
    render(<Panorama ano={2050} aoMudarAno={() => {}} buscar={vi.fn(() => Promise.resolve(serie))} />)
    const legenda = await screen.findByRole('group', { name: 'Séries exibidas' })
    for (const rotulo of Object.values(ESPERADOS)) {
      expect(within(legenda).getByRole('button', { name: rotulo })).toBeInTheDocument()
    }
    for (const id of Object.keys(ESPERADOS)) {
      expect(screen.getByTestId(`reg-${id}`)).toHaveTextContent(ESPERADOS[id])
    }
  })

  it('a gaveta "Como ler o Panorama" usa os mesmos nomes', () => {
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})))
    render(<Gaveta tipo="fontes" ano={2050} aoFechar={() => {}} avisar={() => {}} />)
    const termos = [...screen.getByTestId('como-ler').querySelectorAll('dt')].map((dt) => dt.textContent)
    expect(termos.slice(0, 3)).toEqual(Object.values(ESPERADOS))
  })

  it('nenhum arquivo do front-end usa os nomes antigos dos cenários', () => {
    const antigos = /Método das taxas|Contrafactual \(composição|arranjos de 2026\)/
    const comAntigo = Object.entries(fontes).filter(([, texto]) => antigos.test(texto)).map(([arquivo]) => arquivo)
    expect(comAntigo).toEqual([])
  })
})
