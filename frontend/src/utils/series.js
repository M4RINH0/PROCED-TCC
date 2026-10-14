/* Significado fixo das séries: cor, traço e rótulo (nunca só a cor).
   Verde-petróleo: método das taxas; laranja: contrafactual; azul-cobalto: machine learning. */
export const SERIES = [
  { id: 'taxas', rotulo: 'Método das taxas', curto: 'Taxas', cor: 'teal', traco: 'solid' },
  { id: 'ml_rf', rotulo: 'Machine learning (Random Forest)', curto: 'Random Forest', cor: 'cobalt', traco: 'dashed' },
  { id: 'ml_gb', rotulo: 'Machine learning (Gradient Boosting)', curto: 'Gradient Boosting', cor: 'cobalt', traco: 'dotted' },
  { id: 'contrafactual', rotulo: 'Contrafactual (composição de 2026)', curto: 'Contrafactual', cor: 'orange', traco: 'dashed' },
]

export const ANO_INICIAL = 2026
export const ANO_FINAL = 2070 // horizonte do estudo, o mesmo ano em que termina a projeção da população do IBGE

export const RECORTES = [
  { id: 'chefe_60_mais', rotulo: 'Chefe 60+' },
  { id: 'mononuclear_abaixo_60', rotulo: 'Abaixo de 60' },
]

/* Valores de um cenário ao longo dos anos, sem cálculo: só reorganiza a resposta da API */
export function valoresDoCenario(pontos, id) {
  return pontos.map((p) => ({ ano: p.ano, valor: p.cenarios.find((c) => c.id === id)?.valor ?? null }))
}

/* Séries com valor em algum ano; as que vêm null em todos os anos não aparecem em lugar nenhum */
export function seriesComDado(pontos) {
  return SERIES.filter((s) => pontos.some((p) => p.cenarios.some((c) => c.id === s.id && c.valor !== null)))
}
