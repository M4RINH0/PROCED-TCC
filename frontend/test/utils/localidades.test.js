import { describe, expect, it } from 'vitest'
import { BRASIL, nomeDaLocalidade, regiaoDe } from '../../src/utils/localidades.js'

const REGIOES = [
  { nome: 'Centro-Oeste', estados: [{ sigla: 'DF', nome: 'Distrito Federal' }, { sigla: 'GO', nome: 'Goiás' }] },
  { nome: 'Sul', estados: [{ sigla: 'RS', nome: 'Rio Grande do Sul' }] },
]

describe('regiaoDe', () => {
  it('é nula para o Brasil', () => {
    expect(regiaoDe(REGIOES, BRASIL)).toBeNull()
    expect(regiaoDe(REGIOES, undefined)).toBeNull()
  })
  it('devolve a própria região ou a região do estado', () => {
    expect(regiaoDe(REGIOES, 'Sul')).toBe('Sul')
    expect(regiaoDe(REGIOES, 'DF')).toBe('Centro-Oeste')
  })
  it('é nula para valor desconhecido', () => expect(regiaoDe(REGIOES, 'XX')).toBeNull())
})

describe('nomeDaLocalidade', () => {
  it('usa o nome do estado, da região ou Brasil', () => {
    expect(nomeDaLocalidade(REGIOES, 'GO')).toBe('Goiás')
    expect(nomeDaLocalidade(REGIOES, 'Centro-Oeste')).toBe('Centro-Oeste')
    expect(nomeDaLocalidade(REGIOES, BRASIL)).toBe('Brasil')
  })
  it('mostra o código quando a lista ainda não chegou', () => expect(nomeDaLocalidade([], 'DF')).toBe('DF'))
})
