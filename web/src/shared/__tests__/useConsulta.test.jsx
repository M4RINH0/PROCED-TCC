import { act, renderHook, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { useConsulta } from '../useConsulta.js'

describe('useConsulta', () => {
  it('começa carregando e termina com os dados', async () => {
    const { result } = renderHook(() => useConsulta(() => Promise.resolve({ x: 1 }), []))
    expect(result.current.status).toBe('carregando')
    await waitFor(() => expect(result.current.status).toBe('ok'))
    expect(result.current.dados).toEqual({ x: 1 })
  })

  it('guarda o erro e consulta de novo ao recarregar', async () => {
    const buscar = vi.fn().mockRejectedValueOnce(new Error('falhou')).mockResolvedValue({ x: 2 })
    const { result } = renderHook(() => useConsulta(buscar, []))
    await waitFor(() => expect(result.current.status).toBe('erro'))
    expect(result.current.erro.message).toBe('falhou')
    act(() => result.current.recarregar())
    await waitFor(() => expect(result.current.dados).toEqual({ x: 2 }))
  })

  it('refaz a consulta quando as chaves mudam e cancela a anterior', async () => {
    const sinais = []
    const buscar = vi.fn(({ signal }) => {
      sinais.push(signal)
      return Promise.resolve('ok')
    })
    const { rerender } = renderHook(({ chave }) => useConsulta(buscar, [chave]), { initialProps: { chave: 'a' } })
    rerender({ chave: 'b' })
    await waitFor(() => expect(buscar).toHaveBeenCalledTimes(2))
    expect(sinais[0].aborted).toBe(true)
  })

  it('ignora o cancelamento sem marcar erro', async () => {
    const abort = Object.assign(new Error('x'), { name: 'AbortError' })
    const { result } = renderHook(() => useConsulta(() => Promise.reject(abort), []))
    await new Promise((r) => setTimeout(r, 0))
    expect(result.current.status).toBe('carregando')
  })
})
