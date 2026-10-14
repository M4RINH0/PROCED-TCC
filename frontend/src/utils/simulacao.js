/* Controles de simulação (RF02): limites e padrões iguais aos da API (P13 e P14) */
export const PADRAO_SIMULACAO = { k: 1, intensidade: 0.6 }

export const CONTROLES = {
  k: {
    rotulo: 'Velocidade do envelhecimento (k)',
    min: 0.5,
    max: 1.5,
    passo: 0.1,
    padrao: 'projeção da população do IBGE',
    ajuda: 'Acelera (acima de 1) ou freia (abaixo de 1) o envelhecimento projetado a partir de 2026.',
  },
  intensidade: {
    rotulo: 'Intensidade da mudança de arranjos',
    min: 0,
    max: 1.5,
    passo: 0.1,
    padrao: 'tendência observada nas POFs',
    ajuda: '0 congela os arranjos a partir de 2026.',
  },
}

/* Espera depois do último ajuste antes de consultar a API */
export const ESPERA_MS = 400

export function emSimulacao(valores) {
  return valores.k !== PADRAO_SIMULACAO.k || valores.intensidade !== PADRAO_SIMULACAO.intensidade
}

/* Valor do controle arredondado ao passo (o range do navegador devolve texto) */
export function lerControle(texto) {
  return Math.round(Number(texto) * 10) / 10
}

/* Estado usado quando a página é montada sozinha (testes): padrões e nenhuma ação */
export const SIMULACAO_PADRAO = {
  valores: PADRAO_SIMULACAO,
  aplicados: PADRAO_SIMULACAO,
  ativa: false,
  aoMudar: () => {},
  restaurar: () => {},
}
