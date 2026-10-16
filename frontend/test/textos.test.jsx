import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import Panorama from '../src/pages/Panorama.jsx'
import Simulador from '../src/pages/Simulador.jsx'
import { SERIES } from '../src/utils/series.js'

/* O IBGE projeta só a população: nenhum texto pode chamar o consumo de "oficial" nem atribuí-lo ao IBGE */
const fontes = import.meta.glob('../src/**/*.{js,jsx}', { query: '?raw', import: 'default', eager: true })

/* Únicas formas em que o IBGE pode aparecer: como fonte da população, ou como autor da POF (a pesquisa
   de onde vem o consumo declarado, sem nenhuma projeção de consumo atribuída ao IBGE) */
const IBGE_PERMITIDO = [
  /Projeções da População \(IBGE\)/g,
  /POF 2017 a 2018 \(IBGE\)/g,
  /projeção (populacional|da população) do IBGE/g,
  /O IBGE projeta só a população/g,
]

describe('textos da interface', () => {
  it('lê todos os arquivos do front-end', () => {
    expect(Object.keys(fontes).length).toBeGreaterThanOrEqual(30)
    expect(Object.keys(fontes)).toContain('../src/pages/Panorama.jsx')
  })

  it('nenhum arquivo do front-end usa a palavra "oficial"', () => {
    const comOficial = Object.entries(fontes).filter(([, texto]) => /oficial/i.test(texto)).map(([arquivo]) => arquivo)
    expect(comOficial).toEqual([])
  })

  it('o IBGE só aparece como fonte da população', () => {
    const atribuicoes = Object.entries(fontes).flatMap(([arquivo, texto]) => {
      const limpo = IBGE_PERMITIDO.reduce((t, re) => t.replace(re, ''), texto)
      return limpo.includes('IBGE') ? [arquivo] : []
    })
    expect(atribuicoes).toEqual([])
  })

  it('nenhum rótulo de série cita o IBGE ou uma projeção oficial', () => {
    for (const s of SERIES) {
      expect(`${s.rotulo} ${s.curto}`).not.toMatch(/IBGE|oficial/i)
    }
  })

  it('o Panorama e o Simulador renderizados não falam em consumo oficial', async () => {
    const cenario = (id, valor) => ({ id, valor, consumo_por_pessoa_kwh: valor, consumo_total_calibrado_kwh_mes: valor && 1e9, variacao_kwh: null, variacao_pct: null })
    const serie = {
      fonte: 'POF 2017 a 2018 e Projeções da População (IBGE)',
      domicilios_amostra: 9120,
      celulas: [],
      baixa_confiabilidade: false,
      pontos: Array.from({ length: 45 }, (_, i) => ({
        ano: 2026 + i,
        cenarios: [cenario('taxas', 98), cenario('ml_rf', null), cenario('ml_gb', null), cenario('contrafactual', 97.9)],
        participacao_60_mais_pct: 30,
        efeito_envelhecimento_kwh: 0.1,
        efeito_envelhecimento_total_kwh_mes: 1.2e9,
      })),
    }
    const { unmount } = render(<Panorama ano={2050} aoMudarAno={() => {}} buscar={vi.fn(() => Promise.resolve(serie))} />)
    await screen.findByTestId('reg-taxas')
    expect(document.body.textContent).not.toMatch(/oficial/i)
    unmount()

    const simulacao = (p) => ({
      ...p,
      faixa: '70 a 79',
      valor: 120.5,
      motivo_sem_valor: null,
      domicilios_amostra: 1218,
      baixa_confiabilidade: false,
      domicilios_projetados: 4041963,
      participacao_pct: 4.48,
      consumo_total_calibrado_kwh_mes: 415447972,
      por_faixa: [],
      fonte: 'POF 2017 a 2018 e Projeções da População (IBGE), média ponderada pelo peso amostral',
    })
    render(<Simulador buscar={vi.fn((p) => Promise.resolve(simulacao(p)))} />)
    await screen.findByText('120,5 kWh por mês por pessoa')
    expect(document.body.textContent).not.toMatch(/oficial/i)
  })
})
