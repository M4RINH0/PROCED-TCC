import { apiGet } from '../../shared/index.js'

/* GET /estrutura-etaria/piramide?ano= (RF05) */
export function buscarPiramide({ ano }, opcoes) {
  return apiGet('/estrutura-etaria/piramide', { ano }, opcoes)
}

/* GET /estrutura-etaria/consumo-chefe?arranjo= (RF05, RF06) */
export function buscarConsumoChefe({ arranjo }, opcoes) {
  return apiGet('/estrutura-etaria/consumo-chefe', { arranjo }, opcoes)
}
