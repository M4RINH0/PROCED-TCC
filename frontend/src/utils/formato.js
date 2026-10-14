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

/* Valor com sinal explícito; o sinal de menos é o matemático (U+2212), como no protótipo */
export function comSinal(valor) {
  return (valor >= 0 ? '+' : '−') + umaCasa(Math.abs(valor))
}

/* kWh/mês em milhões, com uma casa: só muda a escala do número que a API devolve */
export function milhoes(valor) {
  return `${umaCasa(valor / 1e6)} milhões`
}
