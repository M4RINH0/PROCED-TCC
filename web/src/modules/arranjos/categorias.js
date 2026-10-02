/* Aparência de cada categoria da grade, na paleta do protótipo */
export const APARENCIA = {
  uni_60: { classe: 'h-u60', cor: 'teal', nome: 'Unipessoal 60+', sub: 'Pessoa idosa morando só' },
  cas_60: { classe: 'h-c60', cor: 'teal-2', nome: 'Casal de idosos', sub: 'Dois moradores, chefe 60+' },
  uni_59: { classe: 'h-u59', cor: 'c3', nome: 'Unipessoal abaixo de 60', sub: 'Grupo de comparação' },
  cas_59: { classe: 'h-csf', cor: 'c4', nome: 'Casal abaixo de 60', sub: 'Grupo de comparação' },
  mul_60: { classe: 'h-out', cor: 'c6', nome: 'Multipessoal 60+', sub: 'Três ou mais moradores' },
  mul_59: { classe: 'h-ccf', cor: 'c7', nome: 'Multipessoal abaixo de 60', sub: 'Arranjo mais numeroso' },
}

export const FILTROS = [
  { id: 'todos', rotulo: 'Todos' },
  { id: 'rec', rotulo: 'Recorte 60+' },
  { id: 'mono', rotulo: 'Mononucleares' },
]

export function noFiltro(categoria, filtro) {
  if (filtro === 'rec') return categoria.mononuclear && categoria.chefe_60_mais
  if (filtro === 'mono') return categoria.mononuclear
  return true
}

/* anos marcados no mini histórico de cada linha */
export const ANOS_HISTORICO = [2026, 2031, 2036, 2041, 2046, 2051, 2056, 2061, 2066, 2070]
