import { apiGet } from '../../shared/index.js'

/* GET /arranjos?grupo= (RF03, RF04) */
export function buscarArranjos({ grupo }, opcoes) {
  return apiGet('/arranjos', { grupo }, opcoes)
}

/* GET /arranjos/composicao: participação de cada arranjo de 2026 a 2070 */
export function buscarComposicao(opcoes) {
  return apiGet('/arranjos/composicao', {}, opcoes)
}
