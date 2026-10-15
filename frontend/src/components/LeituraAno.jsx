import { comSinal, umaCasa } from '../utils/formato.js'
import { INDICADORES, efeitoDoIndicador, valorDoIndicador } from '../utils/indicadores.js'
import Odometro from './Odometro.jsx'

const semDado = (v) => v === null || v === undefined

const EFEITOS = [
  ['envelhecimento', 'Efeito do envelhecimento', 'envelhecimento e arranjos menos sem mudanças desde 2026'],
  ['idade', 'Efeito da idade', 'só o envelhecimento menos sem mudanças desde 2026'],
  ['arranjos', 'Efeito dos arranjos', 'envelhecimento e arranjos menos só o envelhecimento'],
]

/* Painel "Leitura do ano", compacto para caber em telas de 900 px de altura.
   ponto: item da série no ano; series: só as que têm valor em algum ano; indicador: o do gráfico */
export default function LeituraAno({ ponto, ano, series, visiveis, indicador = INDICADORES[0] }) {
  const cenario = (id) => ponto?.cenarios.find((c) => c.id === id)
  return (
    <div className="readout">
      <div className="ro-h">
        <h2 id="h-ro">Leitura do ano</h2>
        <span className="yr num">{ano}</span>
      </div>
      <p className="ro-ind">{indicador.titulo}</p>
      {series.map((s) => {
        const c = cenario(s.id)
        const valor = valorDoIndicador(c, indicador)
        const variacao = indicador.id === 'tbc' && !semDado(c?.variacao_kwh)
        return (
          <div className="reg" key={s.id} data-testid={`reg-${s.id}`} style={{ opacity: visiveis[s.id] ? 1 : 0.4 }}>
            <span className="lb" style={{ color: `var(--${s.cor})` }}>
              <i style={{ borderTopStyle: s.traco }} />
              <span style={{ color: 'var(--ink-2)' }}>{s.rotulo}</span>
            </span>
            <Odometro valor={valor === null ? null : Math.round(valor * 10) / 10} unidade={indicador.unidadeCurta} />
            {(valor === null || variacao) && (
              <span className="dl">
                {valor === null ? 'Sem dado neste ano' : `${comSinal(c.variacao_kwh)} kWh desde 2026 (${comSinal(c.variacao_pct)}%)`}
              </span>
            )}
          </div>
        )
      })}
      <div className="cmp" data-testid="decomposicao">
        {EFEITOS.map(([nome, rotulo, conta]) => {
          const v = efeitoDoIndicador(ponto, nome, indicador)
          return (
            <div key={nome} title={conta}>
              <span>{rotulo}</span>
              <b className="num">{semDado(v) ? 'sem dado' : `${comSinal(v)} ${indicador.unidadeEfeito}`}</b>
            </div>
          )
        })}
        <div>
          <span>Participação 60+ na população</span>
          <b className="num">{semDado(ponto?.participacao_60_mais_pct) ? 'sem dado' : `${umaCasa(ponto.participacao_60_mais_pct)}%`}</b>
        </div>
      </div>
    </div>
  )
}
