/* Cliente HTTP único do front-end. Só fala com a API do PROCED (RNF10). */
const BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')

export class ErroApi extends Error {
  constructor(mensagem, status) {
    super(mensagem)
    this.name = 'ErroApi'
    this.status = status
  }
}

/* Menu Demonstração: simula a API fora do ar para apresentar a recuperação */
let falhaSimulada = false
export function definirFalhaSimulada(ligada) {
  falhaSimulada = Boolean(ligada)
}
export function falhaEstaSimulada() {
  return falhaSimulada
}

export function montarUrl(caminho, parametros = {}, base = BASE) {
  const url = new URL(base + caminho)
  Object.entries(parametros).forEach(([chave, valor]) => {
    if (valor !== undefined && valor !== null) url.searchParams.set(chave, String(valor))
  })
  return url.toString()
}

export async function apiGet(caminho, parametros, { fetcher = fetch, base = BASE, signal } = {}) {
  if (falhaSimulada) throw new ErroApi('Não foi possível conectar à API (falha simulada)', 0)
  let resposta
  try {
    resposta = await fetcher(montarUrl(caminho, parametros, base), { signal })
  } catch (erro) {
    if (erro?.name === 'AbortError') throw erro
    throw new ErroApi('Não foi possível conectar à API', 0)
  }
  if (!resposta.ok) throw new ErroApi(`A API respondeu com o código ${resposta.status}`, resposta.status)
  return resposta.json()
}
