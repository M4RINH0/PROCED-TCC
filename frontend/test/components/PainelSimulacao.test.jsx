import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import PainelSimulacao from '../../src/components/PainelSimulacao.jsx'
import { PADRAO_SIMULACAO, emSimulacao, lerControle } from '../../src/utils/simulacao.js'

const estado = (valores, extra = {}) => ({
  valores,
  aplicados: valores,
  ativa: emSimulacao(valores),
  aoMudar: vi.fn(),
  restaurar: vi.fn(),
  ...extra,
})

describe('PainelSimulacao', () => {
  it('no padrão mostra os rótulos de referência, sem o rótulo de simulação', () => {
    render(<PainelSimulacao simulacao={estado(PADRAO_SIMULACAO)} />)
    const k = screen.getByLabelText('Velocidade do envelhecimento (k)')
    const intensidade = screen.getByLabelText('Intensidade da mudança de arranjos')
    expect([k.min, k.max, k.step, k.value]).toEqual(['0.5', '1.5', '0.1', '1'])
    expect([intensidade.min, intensidade.max, intensidade.step, intensidade.value]).toEqual(['0', '1.5', '0.1', '0.6'])
    expect(screen.getByText('(projeção da população do IBGE)')).toBeInTheDocument()
    expect(screen.getByText('(tendência observada nas POFs)')).toBeInTheDocument()
    expect(screen.queryByTestId('rotulo-simulacao')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Restaurar padrão' })).not.toBeInTheDocument()
  })

  it('fora do padrão mostra "Simulação" e o botão de restaurar', () => {
    const sim = estado({ k: 1.3, intensidade: 0.6 })
    render(<PainelSimulacao simulacao={sim} />)
    expect(screen.getByTestId('rotulo-simulacao')).toHaveTextContent('Simulação')
    expect(screen.getByText('1,3')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Restaurar padrão' }))
    expect(sim.restaurar).toHaveBeenCalled()
  })

  it('avisa o valor do controle arredondado ao passo', () => {
    const sim = estado(PADRAO_SIMULACAO)
    render(<PainelSimulacao simulacao={sim} />)
    fireEvent.change(screen.getByLabelText('Intensidade da mudança de arranjos'), { target: { value: '1.2000000000000002' } })
    expect(sim.aoMudar).toHaveBeenCalledWith('intensidade', 1.2)
  })

  it('desabilita o controle sem efeito na página e explica por quê', () => {
    render(<PainelSimulacao simulacao={estado(PADRAO_SIMULACAO)} semEfeito={{ intensidade: 'A mudança de arranjos não altera esta página.' }} />)
    expect(screen.getByLabelText('Intensidade da mudança de arranjos')).toBeDisabled()
    expect(screen.getByLabelText('Velocidade do envelhecimento (k)')).toBeEnabled()
    expect(screen.getByText('A mudança de arranjos não altera esta página.')).toBeInTheDocument()
  })
})

describe('utilitários da simulação', () => {
  it('reconhece valores fora do padrão', () => {
    expect(emSimulacao({ k: 1, intensidade: 0.6 })).toBe(false)
    expect(emSimulacao({ k: 1, intensidade: 1 })).toBe(true)
    expect(emSimulacao({ k: 0.5, intensidade: 0.6 })).toBe(true)
  })

  it('arredonda o valor do controle a uma casa', () => {
    expect([lerControle('0.30000000000000004'), lerControle('1.5'), lerControle('0')]).toEqual([0.3, 1.5, 0])
  })
})

describe('PainelSimulacao recolhível', () => {
  it('o título recolhe os controles e, recolhido, mostra os valores em uso', () => {
    render(<PainelSimulacao simulacao={estado({ k: 1.3, intensidade: 0.6 })} />)
    const titulo = screen.getByRole('button', { name: 'Parâmetros de simulação' })
    expect(titulo).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByLabelText('Velocidade do envelhecimento (k)')).toBeVisible()
    expect(screen.queryByTestId('resumo-simulacao')).not.toBeInTheDocument()
    fireEvent.click(titulo)
    expect(titulo).toHaveAttribute('aria-expanded', 'false')
    expect(screen.getByLabelText('Velocidade do envelhecimento (k)')).not.toBeVisible()
    expect(screen.getByTestId('resumo-simulacao')).toHaveTextContent('Velocidade 1,3, intensidade 0,6')
    // o rótulo de simulação e o restaurar continuam à vista
    expect(screen.getByTestId('rotulo-simulacao')).toBeInTheDocument()
    fireEvent.click(titulo)
    expect(screen.getByLabelText('Velocidade do envelhecimento (k)')).toBeVisible()
  })

  it('com o estado do App, segue o recolhido global e avisa o clique', () => {
    const alternarRecolhido = vi.fn()
    render(<PainelSimulacao simulacao={estado(PADRAO_SIMULACAO, { recolhido: true, alternarRecolhido })} />)
    const titulo = screen.getByRole('button', { name: 'Parâmetros de simulação' })
    expect(titulo).toHaveAttribute('aria-expanded', 'false')
    expect(screen.getByTestId('resumo-simulacao')).toHaveTextContent('Velocidade 1,0, intensidade 0,6')
    fireEvent.click(titulo)
    expect(alternarRecolhido).toHaveBeenCalledTimes(1)
  })
})
