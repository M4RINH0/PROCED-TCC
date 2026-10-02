/* Formatação brasileira: vírgula decimal e ponto de milhar */
export function umaCasa(valor) {
  return valor.toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })
}

export function inteiro(valor) {
  return Math.round(valor).toLocaleString('pt-BR')
}

export function reais(valor) {
  return valor.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}
