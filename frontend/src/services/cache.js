/* Cache das respostas da API no navegador. Os dados são pré-calculados e não mudam
   durante a visita, então cada consulta só vai à API uma vez.

   Ordem de busca: memória da visita, depois os dados de abertura gravados no build
   (só em produção) e, por último, a API. */
import { ARQUIVO_DADOS_INICIAIS } from './dadosIniciais.js'

const memoria = new Map()
let iniciais = null // promessa do objeto { chave: resposta } dos dados de abertura

/* Baixa o arquivo estático dos dados de abertura; sem ele (desenvolvimento, build sem
   API), devolve um objeto vazio e tudo segue pela API. */
export async function baixarDadosIniciais(fetcher = fetch, url = `${import.meta.env.BASE_URL}${ARQUIVO_DADOS_INICIAIS}`) {
  try {
    const resposta = await fetcher(url)
    if (!resposta.ok) return {}
    const dados = await resposta.json()
    return dados && typeof dados === 'object' ? dados : {}
  } catch {
    return {}
  }
}

function dadosIniciais() {
  if (!iniciais) iniciais = import.meta.env.PROD ? baixarDadosIniciais() : Promise.resolve({})
  return iniciais
}

/* Testes: define os dados de abertura sem baixar o arquivo */
export function definirDadosIniciais(dados) {
  iniciais = Promise.resolve(dados ?? {})
}

/* Cópia da resposta guardada, ou undefined se a consulta nunca foi feita. A cópia evita
   que uma tela altere sem querer o que outra tela vai receber. */
export async function lerCache(chave) {
  if (memoria.has(chave)) return structuredClone(memoria.get(chave))
  const abertura = await dadosIniciais()
  if (Object.hasOwn(abertura, chave)) {
    memoria.set(chave, abertura[chave])
    return structuredClone(abertura[chave])
  }
  return undefined
}

export function guardarCache(chave, dados) {
  memoria.set(chave, structuredClone(dados))
}

export function limparCache() {
  memoria.clear()
  iniciais = null
}
