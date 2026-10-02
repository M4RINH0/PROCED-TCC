/* Todas as chamadas do front-end à API do PROCED, uma função por endpoint */
import { apiGet } from './http.js'

/* Panorama: GET /projecoes/serie?recorte= (RF01, RF11) */
export function buscarSerie({ recorte }, opcoes) {
  return apiGet('/projecoes/serie', { recorte }, opcoes)
}

/* Gaveta API: GET /projecoes?ano=&recorte= (RF11) */
export function buscarProjecao({ ano, recorte }, opcoes) {
  return apiGet('/projecoes', { ano, recorte }, opcoes)
}

/* Domicílios: GET /arranjos?grupo= (RF03, RF04) */
export function buscarArranjos({ grupo }, opcoes) {
  return apiGet('/arranjos', { grupo }, opcoes)
}

/* Domicílios: GET /arranjos/composicao, participação de cada arranjo de 2026 a 2070 */
export function buscarComposicao(opcoes) {
  return apiGet('/arranjos/composicao', {}, opcoes)
}

/* Estrutura etária: GET /estrutura-etaria/piramides, uma pirâmide por ano de 2026 a 2070 (RF05) */
export function buscarPiramides(opcoes) {
  return apiGet('/estrutura-etaria/piramides', {}, opcoes)
}

/* Estrutura etária: GET /estrutura-etaria/consumo-chefe?arranjo= (RF05, RF06) */
export function buscarConsumoChefe({ arranjo }, opcoes) {
  return apiGet('/estrutura-etaria/consumo-chefe', { arranjo }, opcoes)
}

/* Simulador: GET /simulador?ano=&faixa=&arranjo=&base=&taxa= (RF07) */
export function buscarSimulacao({ ano, faixa, arranjo, base, taxa }, opcoes) {
  return apiGet('/simulador', { ano, faixa, arranjo, base, taxa }, opcoes)
}

/* Gaveta Fontes: GET /fontes (RF10) */
export function buscarFontes(opcoes) {
  return apiGet('/fontes', {}, opcoes)
}
