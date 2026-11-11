import { describe, expect, it, vi } from 'vitest'
import { baixarDadosIniciais, definirDadosIniciais, guardarCache, lerCache, limparCache } from '../../src/services/cache.js'

describe('lerCache e guardarCache', () => {
  it('consulta nunca feita devolve undefined', async () => {
    await expect(lerCache('/nada')).resolves.toBeUndefined()
  })

  it('devolve o que foi guardado', async () => {
    guardarCache('/fontes', { fontes: [1, 2] })
    await expect(lerCache('/fontes')).resolves.toEqual({ fontes: [1, 2] })
  })

  it('devolve cópias: alterar o que uma tela recebeu não muda o guardado', async () => {
    const original = { pontos: [{ ano: 2026 }] }
    guardarCache('/serie', original)
    original.pontos.push({ ano: 9999 })
    const primeira = await lerCache('/serie')
    primeira.pontos[0].ano = 0
    await expect(lerCache('/serie')).resolves.toEqual({ pontos: [{ ano: 2026 }] })
  })

  it('usa os dados de abertura quando a memória não tem a consulta', async () => {
    definirDadosIniciais({ '/fontes': { de: 'abertura' } })
    await expect(lerCache('/fontes')).resolves.toEqual({ de: 'abertura' })
  })

  it('a memória tem prioridade sobre os dados de abertura', async () => {
    definirDadosIniciais({ '/fontes': { de: 'abertura' } })
    guardarCache('/fontes', { de: 'api' })
    await expect(lerCache('/fontes')).resolves.toEqual({ de: 'api' })
  })

  it('não confunde propriedades herdadas com consultas', async () => {
    definirDadosIniciais({})
    await expect(lerCache('toString')).resolves.toBeUndefined()
  })

  it('limparCache apaga a memória e os dados de abertura', async () => {
    definirDadosIniciais({ '/a': 1 })
    guardarCache('/b', 2)
    limparCache()
    await expect(lerCache('/a')).resolves.toBeUndefined()
    await expect(lerCache('/b')).resolves.toBeUndefined()
  })

  it('fora de produção não baixa o arquivo de abertura', async () => {
    const fetch = vi.fn()
    vi.stubGlobal('fetch', fetch)
    await lerCache('/qualquer')
    expect(fetch).not.toHaveBeenCalled()
    vi.unstubAllGlobals()
  })
})

describe('baixarDadosIniciais', () => {
  it('devolve o objeto do arquivo', async () => {
    const fetcher = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({ '/fontes': {} }) })
    await expect(baixarDadosIniciais(fetcher, '/dados-iniciais.json')).resolves.toEqual({ '/fontes': {} })
    expect(fetcher).toHaveBeenCalledWith('/dados-iniciais.json')
  })

  it('arquivo ausente (404) vira objeto vazio', async () => {
    const fetcher = vi.fn().mockResolvedValue({ ok: false, status: 404 })
    await expect(baixarDadosIniciais(fetcher, '/x')).resolves.toEqual({})
  })

  it('falha de rede vira objeto vazio', async () => {
    const fetcher = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'))
    await expect(baixarDadosIniciais(fetcher, '/x')).resolves.toEqual({})
  })

  it('conteúdo que não é JSON vira objeto vazio', async () => {
    const fetcher = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.reject(new SyntaxError('html')) })
    await expect(baixarDadosIniciais(fetcher, '/x')).resolves.toEqual({})
  })

  it('JSON que não é objeto vira objeto vazio', async () => {
    const fetcher = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve(null) })
    await expect(baixarDadosIniciais(fetcher, '/x')).resolves.toEqual({})
  })
})
