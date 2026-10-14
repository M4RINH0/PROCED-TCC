/* Significado fixo das séries: cor, traço e rótulo (nunca só a cor).
   Verde-petróleo: método das taxas (cheio com a tendência dos arranjos, tracejado só com o envelhecimento);
   laranja: contrafactual; azul-cobalto: machine learning. */
export const SERIES = [
  { id: 'taxas', rotulo: 'Método das taxas (envelhecimento e arranjos)', curto: 'Taxas', cor: 'teal', traco: 'solid' },
  {
    id: 'taxas_arranjos_fixos',
    rotulo: 'Só o envelhecimento (arranjos de 2026)',
    curto: 'Arranjos fixos',
    cor: 'teal',
    traco: 'dashed',
  },
  { id: 'ml_rf', rotulo: 'Machine learning (Random Forest)', curto: 'Random Forest', cor: 'cobalt', traco: 'dashed' },
  { id: 'ml_gb', rotulo: 'Machine learning (Gradient Boosting)', curto: 'Gradient Boosting', cor: 'cobalt', traco: 'dotted' },
  { id: 'contrafactual', rotulo: 'Contrafactual (composição de 2026)', curto: 'Contrafactual', cor: 'orange', traco: 'dashed' },
]

export const ANO_INICIAL = 2026
export const ANO_FINAL = 2070 // horizonte do estudo, o mesmo ano em que termina a projeção da população do IBGE

/* Recortes do Panorama; o primeiro é o padrão. `explica` diz que efeito cada um mostra */
export const RECORTES = [
  {
    id: 'todos_domicilios',
    rotulo: 'Todos os domicílios',
    explica: 'Mostra os dois efeitos: o da idade, porque a população envelhece, e o dos arranjos, porque muda a divisão entre quem mora só, em dupla ou com mais pessoas.',
  },
  {
    id: 'chefe_60_mais_todos',
    rotulo: 'Chefe 60+, todos os arranjos',
    explica: 'Mostra principalmente o efeito dos arranjos: entre as faixas de 60 anos ou mais, o consumo por pessoa muda pouco com a idade.',
  },
  {
    id: 'chefe_60_mais',
    rotulo: 'Chefe 60+, mononucleares',
    explica: 'Esconde os dois efeitos: o recorte já é definido pela idade do chefe e pelo arranjo, então o envelhecimento quase não muda a média.',
  },
  {
    id: 'mononuclear_abaixo_60',
    rotulo: 'Abaixo de 60, mononucleares',
    explica: 'Esconde os dois efeitos: o recorte já é definido pela idade do chefe e pelo arranjo, então o envelhecimento quase não muda a média.',
  },
]

/* Valores de um cenário ao longo dos anos, sem cálculo: só reorganiza a resposta da API */
export function valoresDoCenario(pontos, id) {
  return pontos.map((p) => ({ ano: p.ano, valor: p.cenarios.find((c) => c.id === id)?.valor ?? null }))
}

/* Séries com valor em algum ano; as que vêm null em todos os anos não aparecem em lugar nenhum */
export function seriesComDado(pontos) {
  return SERIES.filter((s) => pontos.some((p) => p.cenarios.some((c) => c.id === s.id && c.valor !== null)))
}
