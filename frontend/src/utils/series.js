/* Significado fixo das séries: cor, traço e rótulo (nunca só a cor). Os rótulos da interface são simples;
   o texto do TCC mantém os termos técnicos (taxas, taxas_arranjos_fixos, contrafactual).
   Verde-petróleo: método das taxas (cheio com a tendência dos arranjos, tracejado só com o envelhecimento);
   laranja: contrafactual. O machine learning saiu do escopo das projeções (CLAUDE.md). */
export const SERIES = [
  { id: 'taxas', rotulo: 'Envelhecimento e arranjos', curto: 'Envelhecimento e arranjos', cor: 'teal', traco: 'solid' },
  {
    id: 'taxas_arranjos_fixos',
    rotulo: 'Só o envelhecimento',
    curto: 'Só o envelhecimento',
    cor: 'teal',
    traco: 'dashed',
  },
  { id: 'contrafactual', rotulo: 'Sem mudanças desde 2026', curto: 'Sem mudanças desde 2026', cor: 'orange', traco: 'dashed' },
]

/* Rótulo de um cenário na interface; todas as páginas e a gaveta usam este, para o nome ser o mesmo em todo lugar */
export const rotuloDaSerie = (id) => SERIES.find((s) => s.id === id).rotulo

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
    explica: 'Mostra principalmente o efeito dos arranjos. A média por pessoa de um grupo não sobe só porque o grupo cresce: o crescimento dos domicílios de idosos aparece no consumo total e na participação.',
  },
  {
    id: 'chefe_60_mais',
    rotulo: 'Chefe 60+, mononucleares',
    explica: 'Na média por pessoa, esconde os dois efeitos: o recorte já é definido pela idade do chefe e pelo arranjo. A média de um grupo não sobe só porque o grupo cresce; o crescimento aparece no consumo total e na participação.',
  },
  {
    id: 'mononuclear_abaixo_60',
    rotulo: 'Abaixo de 60, mononucleares',
    explica: 'Na média por pessoa, esconde os dois efeitos: o recorte já é definido pela idade do chefe e pelo arranjo. A média de um grupo não sobe só porque o grupo cresce; o crescimento aparece no consumo total e na participação.',
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
