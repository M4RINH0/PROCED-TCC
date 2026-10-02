import { apiGet } from '../../shared/index.js'

/* GET /projecoes?ano=&recorte= (contrato da API, RF11) */
export function buscarProjecao({ ano, recorte }, opcoes) {
  return apiGet('/projecoes', { ano, recorte }, opcoes)
}
