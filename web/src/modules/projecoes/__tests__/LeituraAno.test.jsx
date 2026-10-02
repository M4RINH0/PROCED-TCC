import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import LeituraAno from '../components/LeituraAno.jsx'

describe('LeituraAno', () => {
  it('mostra os três cenários com valor em formato brasileiro', () => {
    render(
      <LeituraAno
        cenarios={[
          { id: 'mod', valor: 230.3 },
          { id: 'ibge', valor: 208.1 },
          { id: 'alt', valor: 1262.3 },
        ]}
      />,
    )
    expect(within(screen.getByTestId('reg-mod')).getByText(/230,3/)).toBeInTheDocument()
    expect(within(screen.getByTestId('reg-alt')).getByText(/1\.262,3/)).toBeInTheDocument()
    expect(screen.getByText('Projeção oficial IBGE')).toBeInTheDocument()
  })

  it('marca a ausência da série oficial depois de 2060 em vez de mostrar um traço', () => {
    render(
      <LeituraAno
        cenarios={[
          { id: 'mod', valor: 230.3 },
          { id: 'ibge', valor: null },
          { id: 'alt', valor: 262.3 },
        ]}
      />,
    )
    expect(within(screen.getByTestId('reg-ibge')).getByText('Sem projeção oficial após 2060')).toBeInTheDocument()
  })

  it('usa "sem dado" para outro cenário ausente', () => {
    render(<LeituraAno cenarios={[{ id: 'mod', valor: 1 }]} />)
    expect(within(screen.getByTestId('reg-alt')).getByText('sem dado')).toBeInTheDocument()
  })

  it('identifica cada série por traço além da cor', () => {
    const { container } = render(<LeituraAno cenarios={[]} />)
    expect(container.querySelectorAll('i.t-mod, i.t-ibge, i.t-alt')).toHaveLength(3)
  })
})
