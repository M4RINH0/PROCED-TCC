/* Dados de abertura: as respostas da API para a visão padrão de cada tela (Brasil,
   controles de simulação no padrão), gravadas no build do front-end num arquivo estático.

   Motivo: no Vercel a API é uma função serverless que desliga quando fica ociosa; ao
   religar, ela relê as tabelas do Supabase e a primeira resposta leva perto de 1 minuto
   (partida a frio). Com este arquivo, a abertura do site não depende dessa espera.

   Nada é calculado aqui: são as respostas da própria API, buscadas durante o build.
   Este módulo não usa import.meta.env porque também roda no Node, dentro do vite.config.js. */
import { ATALHOS } from '../utils/comparacao.js'
import { BRASIL } from '../utils/localidades.js'
import { RECORTES } from '../utils/series.js'
import { PADRAO_SIMULACAO } from '../utils/simulacao.js'

export const ARQUIVO_DADOS_INICIAIS = 'dados-iniciais.json'

/* Chave de uma consulta: o caminho e os parâmetros em ordem alfabética, sem os vazios.
   É a mesma no build e no navegador, independente do endereço da API. */
export function chaveDe(caminho, parametros = {}) {
  const busca = new URLSearchParams()
  Object.entries(parametros)
    .filter(([, valor]) => valor !== undefined && valor !== null)
    .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))
    .forEach(([chave, valor]) => busca.set(chave, String(valor)))
  const texto = busca.toString()
  return texto ? `${caminho}?${texto}` : caminho
}

const { intensidade, k } = PADRAO_SIMULACAO
const LOCAL = { localidade: BRASIL }

/* Arranjos do seletor da Estrutura etária e o formulário inicial do Simulador
   (o teste test/services/dadosIniciais.test.jsx confere que batem com as páginas) */
export const ARRANJOS_CONSUMO_CHEFE = ['mononucleares', 'unipessoal', 'casal_ou_dupla', 'multipessoal', 'todos']
export const SIMULADOR_INICIAL = { ano: 2070, faixa: '70_79', arranjo: 'unipessoal', base: 'taxas' }

/* A visão padrão de cada tela, com os mesmos parâmetros que as páginas enviam */
export const CONSULTAS_INICIAIS = [
  { caminho: '/localidades', parametros: {} },
  { caminho: '/fontes', parametros: {} },
  ...RECORTES.map((r) => ({ caminho: '/projecoes/serie', parametros: { recorte: r.id, ...LOCAL, intensidade, k } })),
  { caminho: '/arranjos/composicao', parametros: { ...LOCAL, intensidade, k } },
  { caminho: '/estrutura-etaria/piramides', parametros: { ...LOCAL, k } },
  ...ARRANJOS_CONSUMO_CHEFE.map((arranjo) => ({ caminho: '/estrutura-etaria/consumo-chefe', parametros: { arranjo, ...LOCAL } })),
  { caminho: '/simulador', parametros: { ...SIMULADOR_INICIAL, ...LOCAL, intensidade, k } },
  ...ATALHOS.map((a) => ({
    caminho: '/comparacao',
    parametros: { grupos: a.grupos.join(','), indicador: 'domicilios', forma: 'indice', cenario: 'taxas', ...LOCAL, intensidade, k },
  })),
  { caminho: '/comparacao/sensibilidade-intensidade', parametros: {} },
  { caminho: '/comparacao/sensibilidade-cobertura', parametros: {} },
  { caminho: '/localidades/sintese-regional', parametros: {} },
]

/* Consultas que obrigam a API a carregar todas as tabelas: usadas para acordá-la */
export const CONSULTAS_AQUECIMENTO = [
  { caminho: '/projecoes/serie', parametros: { recorte: RECORTES[0].id, ...LOCAL, intensidade, k } },
  { caminho: '/estrutura-etaria/piramides', parametros: { ...LOCAL, k } },
]

/* Build: busca cada consulta na API, uma de cada vez (a primeira acorda a função e as
   seguintes já a encontram ligada, sem abrir várias partidas a frio ao mesmo tempo).
   Uma consulta que falhar fica de fora; a tela correspondente consulta a API normalmente. */
export async function gerarDadosIniciais(base, { fetcher = fetch, tempoLimiteMs = 180000, consultas = CONSULTAS_INICIAIS } = {}) {
  const raiz = base.replace(/\/$/, '')
  const dados = {}
  const falhas = []
  for (const { caminho, parametros } of consultas) {
    const chave = chaveDe(caminho, parametros)
    try {
      const resposta = await fetcher(raiz + chave, { signal: AbortSignal.timeout(tempoLimiteMs) })
      if (!resposta.ok) throw new Error(`código ${resposta.status}`)
      dados[chave] = await resposta.json()
    } catch (erro) {
      falhas.push(`${chave} (${erro?.message ?? erro})`)
    }
  }
  return { dados, falhas }
}
