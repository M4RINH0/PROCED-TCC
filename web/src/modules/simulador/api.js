import { apiGet } from '../../shared/index.js'

/* GET /simulador?ano=&faixa=&arranjo=&base=&taxa= (RF07) */
export function buscarSimulacao({ ano, faixa, arranjo, base, taxa }, opcoes) {
  return apiGet('/simulador', { ano, faixa, arranjo, base, taxa }, opcoes)
}

/* Valida o texto da taxa no formato brasileiro (1,7). Devolve o número ou null. */
export function lerTaxa(texto) {
  const bruto = String(texto).trim().replace(',', '.')
  if (!/^\d{1,2}([.]\d{1,2})?$/.test(bruto)) return null
  const valor = parseFloat(bruto)
  return valor >= 0 && valor <= 10 ? valor : null
}
