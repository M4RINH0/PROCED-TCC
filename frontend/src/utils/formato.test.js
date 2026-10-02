import { describe, expect, it } from 'vitest'
import { inteiro, reais, umaCasa } from './formato.js'

describe('umaCasa', () => {
  it('usa vírgula decimal', () => expect(umaCasa(230.3)).toBe('230,3'))
  it('completa com zero', () => expect(umaCasa(158)).toBe('158,0'))
  it('usa ponto de milhar', () => expect(umaCasa(1234.56)).toBe('1.234,6'))
})

describe('inteiro', () => {
  it('arredonda e usa ponto de milhar', () => expect(inteiro(52208.4)).toBe('52.208'))
})

describe('reais', () => {
  it('formata em real brasileiro', () => expect(reais(78.97).replace(/\s/g, ' ')).toBe('R$ 78,97'))
})
