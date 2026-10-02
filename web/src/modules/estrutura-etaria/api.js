import { apiGet } from '../../shared/index.js'

/* GET /estrutura-etaria/piramides: uma pirâmide por ano, de 2026 a 2070 (RF05) */
export function buscarPiramides(opcoes) {
  return apiGet('/estrutura-etaria/piramides', {}, opcoes)
}

/* GET /estrutura-etaria/consumo-chefe?arranjo= (RF05, RF06) */
export function buscarConsumoChefe({ arranjo }, opcoes) {
  return apiGet('/estrutura-etaria/consumo-chefe', { arranjo }, opcoes)
}
