/* Todas as chamadas do front-end à API do PROCED, uma função por endpoint */
import { apiBaixar, apiGet } from './http.js'

/* Panorama: GET /projecoes/serie?recorte= (RF01, RF02, RF11); intensidade e k são os controles de simulação */
export function buscarSerie({ recorte, localidade, intensidade, k }, opcoes) {
  return apiGet('/projecoes/serie', { recorte, localidade, intensidade, k }, opcoes)
}

/* Gaveta API: GET /projecoes?ano=&recorte= (RF11) */
export function buscarProjecao({ ano, recorte, localidade, intensidade, k }, opcoes) {
  return apiGet('/projecoes', { ano, recorte, localidade, intensidade, k }, opcoes)
}

/* Domicílios: GET /arranjos?grupo= (RF03, RF04) */
export function buscarArranjos({ grupo, localidade }, opcoes) {
  return apiGet('/arranjos', { grupo, localidade }, opcoes)
}

/* Domicílios: GET /arranjos/composicao, participação de cada arranjo de 2026 a 2070 (RF02: intensidade e k) */
export function buscarComposicao({ localidade, intensidade, k }, opcoes) {
  return apiGet('/arranjos/composicao', { localidade, intensidade, k }, opcoes)
}

/* Estrutura etária: GET /estrutura-etaria/piramides, uma pirâmide por ano de 2026 a 2070 (RF05; RF02: k) */
export function buscarPiramides({ localidade, k }, opcoes) {
  return apiGet('/estrutura-etaria/piramides', { localidade, k }, opcoes)
}

/* Estrutura etária: GET /estrutura-etaria/consumo-chefe?arranjo= (RF05, RF06) */
export function buscarConsumoChefe({ arranjo, localidade }, opcoes) {
  return apiGet('/estrutura-etaria/consumo-chefe', { arranjo, localidade }, opcoes)
}

/* Simulador: GET /simulador?ano=&faixa=&arranjo=&base= (RF02, RF07, RF09); base = taxas, taxas_arranjos_fixos ou contrafactual */
export function buscarSimulacao({ ano, faixa, arranjo, base, localidade, intensidade, k, recalcular }, opcoes) {
  return apiGet('/simulador', { ano, faixa, arranjo, base, localidade, intensidade, k, recalcular }, opcoes)
}

/* Comparar: GET /comparacao?grupos=&indicador=&forma=&cenario= (RF12; RF02: intensidade e k) */
export function buscarComparacao({ grupos, indicador, forma, cenario, localidade, intensidade, k }, opcoes) {
  return apiGet('/comparacao', { grupos: grupos.join(','), indicador, forma, cenario, localidade, intensidade, k }, opcoes)
}

/* Gaveta Fontes: GET /fontes (RF10) */
export function buscarFontes(opcoes) {
  return apiGet('/fontes', {}, opcoes)
}

/* Filtros: GET /localidades, regiões e estados de cada uma */
export function buscarLocalidades(opcoes) {
  return apiGet('/localidades', {}, opcoes)
}

export function exportarDados({ formato, escopo, ano, recorte, localidade, intensidade, k }, opcoes) {
  return apiBaixar('/exportar', { formato, escopo, ano, recorte, localidade, intensidade, k }, opcoes)
}

/* Comparar: GET /exportar/comparacao, os mesmos parâmetros de /comparacao mais o formato (RF08, RF12) */
export function exportarComparacao({ formato, grupos, indicador, forma, cenario, localidade, intensidade, k }, opcoes) {
  return apiBaixar('/exportar/comparacao', { formato, grupos: grupos.join(','), indicador, forma, cenario, localidade, intensidade, k }, opcoes)
}
