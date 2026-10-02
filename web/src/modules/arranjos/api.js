import { apiGet } from '../../shared/index.js'

/* GET /arranjos?grupo= (RF03, RF04) */
export function buscarArranjos({ grupo }, opcoes) {
  return apiGet('/arranjos', { grupo }, opcoes)
}
