import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { useAdiado } from '../../src/hooks/useAdiado.js'

describe('useAdiado', () => {
  beforeEach(() => vi.useFakeTimers())
  afterEach(() => vi.useRealTimers())

  it('só entrega o valor depois da espera sem mudanças', () => {
    const { result, rerender } = renderHook(({ v }) => useAdiado(v, 400), { initialProps: { v: 1 } })
    expect(result.current).toBe(1)
    rerender({ v: 1.1 })
    rerender({ v: 1.2 })
    act(() => vi.advanceTimersByTime(399))
    expect(result.current).toBe(1)
    rerender({ v: 1.3 })  // nova mudança reinicia a espera
    act(() => vi.advanceTimersByTime(399))
    expect(result.current).toBe(1)
    act(() => vi.advanceTimersByTime(1))
    expect(result.current).toBe(1.3)  // passos intermediários (1,1 e 1,2) nunca foram entregues
  })
})
