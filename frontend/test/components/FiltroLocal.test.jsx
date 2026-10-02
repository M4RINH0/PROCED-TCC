import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import FiltroLocal from '../../src/components/FiltroLocal.jsx'

const REGIOES = [
  { nome: 'Centro-Oeste', estados: [{ sigla: 'DF', nome: 'Distrito Federal' }, { sigla: 'GO', nome: 'Goiás' }] },
  { nome: 'Sul', estados: [{ sigla: 'RS', nome: 'Rio Grande do Sul' }] },
]
const montar = (valor, aoMudar = vi.fn()) => {
  render(<FiltroLocal local={{ valor, regioes: REGIOES, aoMudar }} />)
  return aoMudar
}

describe('FiltroLocal', () => {
  it('no Brasil, o estado fica bloqueado até escolher a região', () => {
    montar('Brasil')
    expect(screen.getByLabelText('Região')).toHaveValue('Brasil')
    expect(screen.getByLabelText('Estado')).toBeDisabled()
    expect(screen.getByRole('option', { name: 'Escolha a região' })).toBeInTheDocument()
  })

  it('escolher a região filtra pela região inteira', () => {
    const aoMudar = montar('Brasil')
    fireEvent.change(screen.getByLabelText('Região'), { target: { value: 'Sul' } })
    expect(aoMudar).toHaveBeenCalledWith('Sul')
  })

  it('com a região escolhida, lista só os estados dela', () => {
    const aoMudar = montar('Centro-Oeste')
    const estado = screen.getByLabelText('Estado')
    expect(estado).toBeEnabled()
    expect(estado).toHaveValue('Centro-Oeste')
    expect([...estado.options].map((o) => o.textContent)).toEqual(['Todos da região', 'Distrito Federal', 'Goiás'])
    fireEvent.change(estado, { target: { value: 'DF' } })
    expect(aoMudar).toHaveBeenCalledWith('DF')
  })

  it('com um estado escolhido, mostra a região dele e o estado', () => {
    montar('RS')
    expect(screen.getByLabelText('Região')).toHaveValue('Sul')
    expect(screen.getByLabelText('Estado')).toHaveValue('RS')
  })

  it('voltar ao Brasil limpa o estado', () => {
    const aoMudar = montar('DF')
    fireEvent.change(screen.getByLabelText('Região'), { target: { value: 'Brasil' } })
    expect(aoMudar).toHaveBeenCalledWith('Brasil')
  })
})
