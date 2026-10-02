import { apiGet } from '../../shared/index.js'

/* GET /projecoes/serie?recorte= (RF01, RF11) */
export function buscarSerie({ recorte }, opcoes) {
  return apiGet('/projecoes/serie', { recorte }, opcoes)
}

/* Valores de um cenário ao longo dos anos, sem cálculo: só reorganiza a resposta */
export function valoresDoCenario(pontos, id) {
  return pontos.map((p) => ({ ano: p.ano, valor: p.cenarios.find((c) => c.id === id)?.valor ?? null }))
}
