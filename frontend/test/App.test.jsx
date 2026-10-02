import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import App from '../src/App.jsx'

describe('App', () => {
  beforeEach(() => {
    window.location.hash = ''
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})))
  })

  it('abre no Panorama com a aba marcada', () => {
    render(<App />)
    expect(screen.getByRole('heading', { level: 1, name: 'Panorama da projeção' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Panorama' })).toHaveAttribute('aria-current', 'page')
  })

  it.each([
    ['Domicílios', 'Domicílios por arranjo'],
    ['Estrutura etária', 'Estrutura etária'],
    ['Simulador', 'Simulador de cenário'],
  ])('navega para a aba %s', (aba, titulo) => {
    render(<App />)
    fireEvent.click(screen.getByRole('button', { name: aba }))
    expect(screen.getByRole('heading', { level: 1, name: titulo })).toBeInTheDocument()
    expect(window.location.hash).not.toBe('')
  })

  it('alterna o tema no elemento raiz', () => {
    render(<App />)
    const antes = document.documentElement.dataset.theme
    fireEvent.click(screen.getByRole('button', { name: /tema/i }))
    expect(document.documentElement.dataset.theme).not.toBe(antes)
  })

  it('não exibe mais o selo de dados ilustrativos', () => {
    render(<App />)
    expect(screen.queryByText('Dados ilustrativos')).not.toBeInTheDocument()
  })
})
