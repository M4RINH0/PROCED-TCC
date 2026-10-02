import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import EstadoConsulta from './EstadoConsulta.jsx'
import Segmentado from './Segmentado.jsx'

describe('EstadoConsulta', () => {
  it('mostra o carregamento só quando ainda não há dados', () => {
    const { rerender } = render(<EstadoConsulta status="carregando" temDados={false} />)
    expect(screen.getByLabelText('Carregando dados')).toBeInTheDocument()
    rerender(<EstadoConsulta status="carregando" temDados />)
    expect(screen.queryByLabelText('Carregando dados')).not.toBeInTheDocument()
  })

  it('mostra o erro com os parâmetros e permite tentar de novo', () => {
    const tentar = vi.fn()
    render(
      <EstadoConsulta status="erro" erro={new Error('A API respondeu com o código 503')} parametros="ano 2050" aoTentarDeNovo={tentar} />,
    )
    expect(screen.getByRole('alert')).toHaveTextContent('código 503')
    expect(screen.getByRole('alert')).toHaveTextContent('ano 2050')
    fireEvent.click(screen.getByRole('button', { name: 'Tentar novamente' }))
    expect(tentar).toHaveBeenCalledOnce()
  })

  it('não mostra nada quando a consulta deu certo', () => {
    const { container } = render(<EstadoConsulta status="ok" temDados />)
    expect(container).toBeEmptyDOMElement()
  })
})

describe('Segmentado', () => {
  it('marca a opção atual e avisa a escolha', () => {
    const aoMudar = vi.fn()
    render(
      <Segmentado
        rotulo="Grupo"
        valor="a"
        aoMudar={aoMudar}
        opcoes={[
          { id: 'a', rotulo: 'Opção A' },
          { id: 'b', rotulo: 'Opção B' },
        ]}
      />,
    )
    expect(screen.getByRole('button', { name: 'Opção A' })).toHaveAttribute('aria-pressed', 'true')
    fireEvent.click(screen.getByRole('button', { name: 'Opção B' }))
    expect(aoMudar).toHaveBeenCalledWith('b')
  })
})
