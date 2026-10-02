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

/* Valida o texto da taxa no formato brasileiro (1,7). Devolve o número ou null. */
export function lerTaxa(texto) {
  const bruto = String(texto).trim().replace(',', '.')
  if (!/^\d{1,2}([.]\d{1,2})?$/.test(bruto)) return null
  const valor = parseFloat(bruto)
  return valor >= 0 && valor <= 10 ? valor : null
}
