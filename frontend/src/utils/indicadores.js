/* Indicadores do gráfico do Panorama. Todos vêm prontos da API; aqui só se escolhe o campo e a
   escala de exibição (o consumo total aparece em bilhões de kWh/mês). `efeito` é o sufixo dos campos
   da decomposição na resposta (efeito_idade_kwh, efeito_idade_total_kwh_mes...). */
export const INDICADORES = [
  {
    id: 'tbc',
    rotulo: 'Consumo por pessoa (TBC)',
    titulo: 'Consumo por pessoa',
    campo: 'valor',
    unidade: 'kWh/mês por pessoa',
    unidadeCurta: 'kWh',
    escala: 1,
    sufixo: '',
    eixo: { folga: 1, passo: 10 },
    efeito: '_kwh',
    unidadeEfeito: 'kWh por pessoa',
  },
  {
    id: 'total',
    rotulo: 'Consumo total do recorte',
    titulo: 'Consumo total do recorte',
    campo: 'consumo_total_calibrado_kwh_mes',
    unidade: 'bilhões de kWh/mês',
    unidadeCurta: 'bi kWh',
    escala: 1e9,
    sufixo: '',
    eixo: { folga: 0.1, passo: 1 },
    efeito: '_total_kwh_mes',
    unidadeEfeito: 'bilhões de kWh/mês',
  },
  {
    id: 'participacao',
    rotulo: 'Participação no consumo residencial',
    titulo: 'Participação no consumo residencial',
    campo: 'participacao_consumo_pct',
    unidade: '% do consumo residencial',
    unidadeCurta: '%',
    escala: 1,
    sufixo: '%',
    eixo: { folga: 0.5, passo: 5 },
    efeito: '_participacao_pp',
    unidadeEfeito: 'pontos percentuais',
  },
]

/* "Todos os domicílios" abre no consumo por pessoa; os outros recortes, na participação,
   porque a média por pessoa de um grupo não sobe só porque o grupo cresce */
export function indicadorPadrao(recorte) {
  return recorte === 'todos_domicilios' ? 'tbc' : 'participacao'
}

/* Em "todos os domicílios" a participação é sempre 100% */
export function indicadorDisponivel(indicador, recorte) {
  return !(indicador === 'participacao' && recorte === 'todos_domicilios')
}

export function porId(id) {
  return INDICADORES.find((i) => i.id === id) ?? INDICADORES[0]
}

/* Valor do indicador num cenário, na escala de exibição (sem cálculo de taxa: só a unidade muda) */
export function valorDoIndicador(cenario, indicador) {
  const v = cenario?.[indicador.campo]
  return v === null || v === undefined ? null : v / indicador.escala
}

/* Série de um cenário ao longo dos anos para o indicador escolhido */
export function serieDoIndicador(pontos, id, indicador) {
  return pontos.map((p) => ({ ano: p.ano, valor: valorDoIndicador(p.cenarios.find((c) => c.id === id), indicador) }))
}

/* Efeito da decomposição no indicador, na escala de exibição */
export function efeitoDoIndicador(ponto, nome, indicador) {
  const v = ponto?.[`efeito_${nome}${indicador.efeito}`]
  return v === null || v === undefined ? null : v / indicador.escala
}
