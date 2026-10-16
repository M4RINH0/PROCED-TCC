/* Página Comparar (RF12): grupos, atalhos, indicadores e o estilo de cada linha.
   Os valores vêm prontos da API (/comparacao); aqui só há escolhas da interface. */

/* As seis células e os quatro agregados, na ordem da seleção */
export const GRUPOS = [
  { id: 'uni_60', rotulo: 'Unipessoal 60+', arranjo: 'unipessoal', idoso: true },
  { id: 'cas_60', rotulo: 'Casal ou dupla 60+', arranjo: 'casal_ou_dupla', idoso: true },
  { id: 'mul_60', rotulo: 'Multipessoal 60+', arranjo: 'multipessoal', idoso: true },
  { id: 'uni_59', rotulo: 'Unipessoal abaixo de 60', arranjo: 'unipessoal', idoso: false },
  { id: 'cas_59', rotulo: 'Casal ou dupla abaixo de 60', arranjo: 'casal_ou_dupla', idoso: false },
  { id: 'mul_59', rotulo: 'Multipessoal abaixo de 60', arranjo: 'multipessoal', idoso: false },
  { id: 'mono_60', rotulo: 'Mononuclear 60+', arranjo: null, idoso: true },
  { id: 'mono_59', rotulo: 'Mononuclear abaixo de 60', arranjo: null, idoso: false },
  { id: 'todos_60', rotulo: 'Todos 60+', arranjo: null, idoso: true },
  { id: 'todos_59', rotulo: 'Todos abaixo de 60', arranjo: null, idoso: false },
]
export const MINIMO_GRUPOS = 2
export const MAXIMO_GRUPOS = 6

export const ATALHOS = [
  { id: 'arranjos_60', rotulo: 'Arranjos com chefe 60+', grupos: ['uni_60', 'cas_60', 'mul_60'] },
  { id: 'multi', rotulo: '60+ contra abaixo de 60 no multipessoal', grupos: ['mul_60', 'mul_59'] },
  { id: 'mono', rotulo: 'Mononucleares: 60+ contra abaixo de 60', grupos: ['mono_60', 'mono_59'] },
  { id: 'todos', rotulo: 'Todos: 60+ contra abaixo de 60', grupos: ['todos_60', 'todos_59'] },
]
export const GRUPOS_PADRAO = ATALHOS[0].grupos

export const INDICADORES_COMPARACAO = [
  { id: 'domicilios', rotulo: 'Número de domicílios', curto: 'domicílios' },
  { id: 'consumo_total', rotulo: 'Consumo total', curto: 'kWh/mês' },
  { id: 'participacao', rotulo: 'Participação no consumo residencial', curto: '%' },
  { id: 'consumo_por_pessoa', rotulo: 'Consumo por pessoa (só agregados)', curto: 'kWh/mês por pessoa', soAgregados: true },
]
export const FORMAS = [
  { id: 'indice', rotulo: 'Índice (2026 = 100)' },
  { id: 'absoluto', rotulo: 'Valores absolutos' },
]

export const grupoPorId = (id) => GRUPOS.find((g) => g.id === id)
export const soAgregados = (ids) => ids.length > 0 && ids.every((id) => grupoPorId(id).arranjo === null)

/* Estilo da linha: cor pelo arranjo (sem verde-petróleo e sem laranja, que são cenários), traço pela
   idade (cheio 60+, tracejado abaixo de 60) e agregados em tom neutro com traço mais grosso. */
export function estiloDoGrupo(id) {
  const g = grupoPorId(id)
  return {
    cor: g.arranjo ? `var(--g-${g.arranjo})` : 'var(--g-agregado)',
    tracejado: g.idoso ? undefined : '7 5',
    espessura: g.arranjo ? 2.2 : 3.6,
  }
}

/* Marcas do eixo: passos "redondos" (1, 2, 2,5 ou 5 vezes uma potência de 10) cobrindo o intervalo */
export function escalaY(valores, quantidade = 5) {
  const vs = valores.filter((v) => v !== null && v !== undefined)
  if (!vs.length) return { lo: 0, hi: 1, marcas: [0, 1] }
  let lo = Math.min(...vs)
  let hi = Math.max(...vs)
  if (lo === hi) {
    lo -= Math.abs(lo) * 0.05 || 1
    hi += Math.abs(hi) * 0.05 || 1
  }
  const bruto = (hi - lo) / quantidade
  const potencia = 10 ** Math.floor(Math.log10(bruto))
  const passo = [1, 2, 2.5, 5, 10].map((f) => f * potencia).find((p) => p >= bruto)
  const inicio = Math.floor(lo / passo) * passo
  const fim = Math.ceil(hi / passo) * passo
  const marcas = []
  for (let v = inicio; v <= fim + passo / 1e6; v += passo) marcas.push(Math.round(v / passo) * passo)
  return { lo: inicio, hi: fim, marcas }
}

/* Frase-resumo com os números da tabela da API: quem cresce mais contra quem cresce menos */
export function fraseResumo(tabela, cenario) {
  const ordenados = tabela.filter((l) => l.ordem !== null).sort((a, b) => a.ordem - b.ordem)
  if (ordenados.length < 2) return null
  const abs = (v) => `${Math.abs(v).toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%`
  const maior = ordenados[0]
  const menor = ordenados[ordenados.length - 1]
  const primeiro = maior.variacao_pct >= 0 ? `cresce ${abs(maior.variacao_pct)}` : `cai ${abs(maior.variacao_pct)}`
  const segundo = menor.variacao_pct >= 0 ? abs(menor.variacao_pct) : `queda de ${abs(menor.variacao_pct)}`
  return {
    maior,
    menor,
    texto: `De 2026 a 2070, no cenário ${cenario.toLowerCase()}, o grupo ${maior.rotulo.toLowerCase()} ${primeiro}, contra ${segundo} do grupo ${menor.rotulo.toLowerCase()}.`,
  }
}

/* Valor da tabela no formato brasileiro do indicador; sem valor, "sem dado" */
const CASAS = { domicilios: 0, consumo_total: 0, participacao: 2, consumo_por_pessoa: 1 }
export function formatarValor(valor, indicador, { sinal = false, casas: forcadas } = {}) {
  if (valor === null || valor === undefined) return 'sem dado'
  const casas = forcadas ?? CASAS[indicador] ?? 1
  const texto = Math.abs(valor).toLocaleString('pt-BR', { minimumFractionDigits: casas, maximumFractionDigits: casas })
  if (!sinal) return valor < 0 ? `−${texto}` : texto
  return `${valor >= 0 ? '+' : '−'}${texto}`
}

/* Variação percentual com sinal e uma casa */
export const formatarPct = (valor) => (valor === null || valor === undefined ? 'sem dado' : `${formatarValor(valor, null, { sinal: true, casas: 1 })}%`)
