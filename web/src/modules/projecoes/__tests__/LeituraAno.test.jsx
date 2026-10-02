import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import LeituraAno, { textoSemValor } from '../components/LeituraAno.jsx'

describe('LeituraAno', () => {
  it('mostra o valor em formato brasileiro', () => {
    render(<LeituraAno cenarios={[{ id: 'ibge', valor: 1094.3 }]} modelados={['ibge']} />)
    expect(within(screen.getByTestId('reg-ibge')).getByText(/1\.094,3/)).toBeInTheDocument()
  })

  it('marca a ausência da série oficial depois de 2070 em vez de mostrar um traço', () => {
    render(<LeituraAno cenarios={[{ id: 'ibge', valor: null }]} modelados={['ibge']} />)
    expect(within(screen.getByTestId('reg-ibge')).getByText('Sem projeção oficial após 2070')).toBeInTheDocument()
  })

  it('diz que o cenário ainda não foi modelado quando não tem valor em nenhum ano', () => {
    render(<LeituraAno cenarios={[{ id: 'mod', valor: null }]} modelados={['ibge']} />)
    expect(within(screen.getByTestId('reg-mod')).getByText('Cenário ainda não modelado')).toBeInTheDocument()
    expect(within(screen.getByTestId('reg-alt')).getByText('Cenário ainda não modelado')).toBeInTheDocument()
  })

  it('identifica cada série por traço além da cor', () => {
    const { container } = render(<LeituraAno cenarios={[]} />)
    expect(container.querySelectorAll('i.t-mod, i.t-ibge, i.t-alt')).toHaveLength(3)
  })
})

describe('textoSemValor', () => {
  it('usa "sem dado" para cenário modelado sem valor no ano', () => {
    expect(textoSemValor('mod', true)).toBe('sem dado')
  })
})
