import { describe, expect, it } from 'vitest'
import { lerTema, salvarTema, temaEfetivo } from './tema.js'

const memoria = () => {
  const dados = {}
  return { getItem: (k) => dados[k] ?? null, setItem: (k, v) => (dados[k] = v) }
}
const quebrado = { getItem: () => { throw new Error('bloqueado') }, setItem: () => { throw new Error('bloqueado') } }

describe('tema', () => {
  it('salva e lê o tema escolhido', () => {
    const m = memoria()
    salvarTema('dark', m)
    expect(lerTema(m)).toBe('dark')
  })
  it('ignora valor inválido guardado', () => {
    const m = memoria()
    m.setItem('pe-theme', 'roxo')
    expect(lerTema(m)).toBeNull()
  })
  it('não quebra quando o armazenamento falha', () => {
    expect(lerTema(quebrado)).toBeNull()
    expect(() => salvarTema('light', quebrado)).not.toThrow()
  })
  it('usa a preferência do sistema quando não há escolha', () => {
    expect(temaEfetivo(null, true)).toBe('dark')
    expect(temaEfetivo(null, false)).toBe('light')
    expect(temaEfetivo('light', true)).toBe('light')
  })
})
