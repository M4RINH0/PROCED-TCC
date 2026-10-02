import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import EmConstrucao from '../components/EmConstrucao.jsx'

describe('EmConstrucao', () => {
  it('mostra o título e os requisitos da tela', () => {
    render(<EmConstrucao titulo="Simulador" requisitos="RF07 e RF09" />)
    expect(screen.getByRole('heading', { level: 1, name: 'Simulador' })).toBeInTheDocument()
    expect(screen.getByText('Atende RF07 e RF09.')).toBeInTheDocument()
    expect(screen.getByText('Tela em construção')).toBeInTheDocument()
  })
})
