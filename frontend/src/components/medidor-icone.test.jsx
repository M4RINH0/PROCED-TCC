import { render, renderHook, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { useTamanho } from '../hooks/useTamanho.js'
import { apiGet, definirFalhaSimulada, falhaEstaSimulada } from '../services/http.js'
import { comSinal } from '../utils/formato.js'
import Icone from './Icone.jsx'
import Odometro, { digitos } from './Odometro.jsx'

describe('Odometro', () => {
  it('separa os dígitos no formato 000,0', () => {
    expect(digitos(94.3)).toEqual([0, 9, 4, 3])
    expect(digitos(1234)).toEqual([9, 9, 9, 9])
    expect(digitos(-5)).toEqual([0, 0, 0, 0])
  })

  it('rola cada coluna até o dígito e apaga os zeros à esquerda', () => {
    const { container } = render(<Odometro valor={94.3} unidade="kWh/mês" />)
    const colunas = container.querySelectorAll('.dg')
    expect([...colunas].map((c) => c.firstChild.style.transform)).toEqual([
      'translateY(0em)',
      'translateY(-9em)',
      'translateY(-4em)',
      'translateY(-3em)',
    ])
    expect(colunas[0]).toHaveClass('lz')
    expect(colunas[1]).not.toHaveClass('lz')
  })

  it('anuncia o valor para leitores de tela e "sem dado" quando falta', () => {
    const { rerender } = render(<Odometro valor={94.3} unidade="kWh/mês" />)
    expect(screen.getByText('94,3 kWh/mês')).toHaveClass('sr')
    rerender(<Odometro valor={null} unidade="kWh/mês" />)
    expect(screen.getByText('sem dado')).toHaveClass('sr')
  })
})

describe('Icone', () => {
  it('desenha o ícone pedido sem ser anunciado', () => {
    const { container } = render(<Icone nome="db" />)
    expect(container.querySelector('svg')).toHaveAttribute('aria-hidden', 'true')
    expect(container.querySelector('[data-icone="db"]')).toBeInTheDocument()
  })
  it('tem formas próprias para logo, play e pausa', () => {
    ;['logo', 'play', 'pause'].forEach((nome) => {
      const { container } = render(<Icone nome={nome} />)
      expect(container.querySelector('svg path, svg rect')).toBeInTheDocument()
    })
  })
})

describe('comSinal', () => {
  it('usa + e o sinal de menos matemático', () => {
    expect(comSinal(0.3)).toBe('+0,3')
    expect(comSinal(-1.5)).toBe('−1,5')
    expect(comSinal(0)).toBe('+0,0')
  })
})

describe('falha simulada', () => {
  afterEach(() => definirFalhaSimulada(false))
  it('faz a API falhar sem chamar a rede', async () => {
    const fetcher = vi.fn()
    definirFalhaSimulada(true)
    expect(falhaEstaSimulada()).toBe(true)
    await expect(apiGet('/x', {}, { fetcher, base: 'http://api' })).rejects.toMatchObject({ name: 'ErroApi', status: 0 })
    expect(fetcher).not.toHaveBeenCalled()
  })
})

describe('useTamanho', () => {
  it('usa o tamanho padrão quando o elemento ainda não tem medida', () => {
    const { result } = renderHook(() => useTamanho({ largura: 320, altura: 200 }))
    expect(result.current[1]).toEqual({ largura: 320, altura: 200 })
  })
})
