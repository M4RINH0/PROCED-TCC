import { describe, expect, it } from 'vitest'
import { umaCasa } from '../formato.js'

describe('umaCasa', () => {
  it('usa vírgula decimal', () => expect(umaCasa(230.3)).toBe('230,3'))
  it('completa com zero', () => expect(umaCasa(158)).toBe('158,0'))
  it('usa ponto de milhar', () => expect(umaCasa(1234.56)).toBe('1.234,6'))
})
