import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import AvisoAmostra from '../../src/components/AvisoAmostra.jsx'

const celulas = [
  { faixa: '80+', arranjo: 'Unipessoal (Mononuclear)', domicilios_amostra: 3, baixa_confiabilidade: true },
  { faixa: '60 a 69', arranjo: 'Casal ou Dupla', domicilios_amostra: 1200, baixa_confiabilidade: false },
]

describe('AvisoAmostra', () => {
  it('não aparece quando a API não marca baixa confiabilidade', () => {
    render(<AvisoAmostra ativo={false} celulas={celulas} />)
    expect(screen.queryByTestId('aviso-amostra')).not.toBeInTheDocument()
  })

  it('lista só as células marcadas, com o tamanho da amostra', () => {
    render(<AvisoAmostra ativo celulas={celulas} />)
    const aviso = screen.getByTestId('aviso-amostra')
    expect(aviso).toHaveTextContent('menos de 30 domicílios')
    expect(aviso).toHaveTextContent('80+, unipessoal (mononuclear): 3')
    expect(aviso).not.toHaveTextContent('60 a 69')
  })

  it('funciona sem a lista de células', () => {
    render(<AvisoAmostra ativo />)
    expect(screen.getByTestId('aviso-amostra')).toHaveTextContent('Baixa confiabilidade')
  })
})
