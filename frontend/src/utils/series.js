/* Significado fixo das séries: cor, traço e rótulo (nunca só a cor) */
export const SERIES = [
  { id: 'mod', rotulo: 'Projeção do modelo', curto: 'Modelo', cor: 'teal', traco: 'solid' },
  { id: 'ibge', rotulo: 'Projeção oficial IBGE', curto: 'IBGE oficial', cor: 'orange', traco: 'dashed' },
  { id: 'alt', rotulo: 'Cenário alternativo (ML)', curto: 'Alternativo', cor: 'cobalt', traco: 'dotted' },
]

export const ANO_INICIAL = 2026
export const ANO_FINAL = 2070 // horizonte do estudo, o mesmo ano em que termina a projeção do IBGE

export const RECORTES = [
  { id: 'chefe_60_mais', rotulo: 'Chefe 60+' },
  { id: 'mononuclear_abaixo_60', rotulo: 'Abaixo de 60' },
]

/* Valores de um cenário ao longo dos anos, sem cálculo: só reorganiza a resposta da API */
export function valoresDoCenario(pontos, id) {
  return pontos.map((p) => ({ ano: p.ano, valor: p.cenarios.find((c) => c.id === id)?.valor ?? null }))
}
