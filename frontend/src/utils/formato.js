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

/* Número grande em escala curta para eixos (mil, mi, bi), com uma casa: só muda a escala */
export function compacto(valor) {
  const abs = Math.abs(valor)
  if (abs >= 1e9) return `${umaCasa(valor / 1e9)} bi`
  if (abs >= 1e6) return `${umaCasa(valor / 1e6)} mi`
  if (abs >= 1e4) return `${umaCasa(valor / 1e3)} mil`
  return Number.isInteger(valor) ? valor.toLocaleString('pt-BR') : umaCasa(valor)
}
