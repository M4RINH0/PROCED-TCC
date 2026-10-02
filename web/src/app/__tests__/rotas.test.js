import { describe, expect, it } from 'vitest'
import { ROTA_PADRAO, ROTAS, rotaDoHash } from '../rotas.js'

describe('rotaDoHash', () => {
  it('reconhece cada rota pelo hash', () => {
    ROTAS.forEach((r) => expect(rotaDoHash('#' + r.id)).toBe(r.id))
  })
  it('aceita o id sem o caractere #', () => expect(rotaDoHash('sim')).toBe('sim'))
  it('cai no Panorama quando o hash é vazio ou desconhecido', () => {
    expect(rotaDoHash('')).toBe(ROTA_PADRAO)
    expect(rotaDoHash('#xyz')).toBe(ROTA_PADRAO)
    expect(rotaDoHash(undefined)).toBe('pan')
  })
})
