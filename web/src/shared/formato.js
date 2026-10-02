/* Formatação brasileira: vírgula decimal e ponto de milhar */
export function umaCasa(valor) {
  return valor.toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })
}
