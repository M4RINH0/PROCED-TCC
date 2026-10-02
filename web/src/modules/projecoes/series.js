/* Significado fixo das séries: cor, traço e rótulo (nunca só a cor) */
export const SERIES = [
  { id: 'mod', rotulo: 'Projeção do modelo', curto: 'Modelo', cor: 'teal', traco: 'solid' },
  { id: 'ibge', rotulo: 'Projeção oficial IBGE', curto: 'IBGE oficial', cor: 'orange', traco: 'dashed' },
  { id: 'alt', rotulo: 'Cenário alternativo (ML)', curto: 'Alternativo', cor: 'cobalt', traco: 'dotted' },
]

export const ANO_INICIAL = 2026
export const ANO_FINAL = 2075
export const ANO_FINAL_IBGE = 2070

export const RECORTES = [
  { id: 'chefe_60_mais', rotulo: 'Chefe 60+' },
  { id: 'mononuclear_abaixo_60', rotulo: 'Abaixo de 60' },
]
