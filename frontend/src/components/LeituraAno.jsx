import { comSinal, milhoes, umaCasa } from '../utils/formato.js'
import Odometro from './Odometro.jsx'

const semDado = (v) => v === null || v === undefined
const sinal = (v) => (v >= 0 ? '+' : '−')

/* Painel "Leitura do ano". ponto: item da série no ano; series: só as que têm valor em algum ano */
export default function LeituraAno({ ponto, ano, series, visiveis }) {
  const cenario = (id) => ponto?.cenarios.find((c) => c.id === id)
  const taxas = cenario('taxas')
  return (
    <div className="readout">
      <div className="ro-h">
        <h2 id="h-ro">Leitura do ano</h2>
        <span className="yr num">{ano}</span>
      </div>
      {series.map((s) => {
        const c = cenario(s.id)
        const valor = c?.valor ?? null
        return (
          <div className="reg" key={s.id} data-testid={`reg-${s.id}`} style={{ opacity: visiveis[s.id] ? 1 : 0.4 }}>
            <span className="lb" style={{ color: `var(--${s.cor})` }}>
              <i style={{ borderTopStyle: s.traco }} />
              <span style={{ color: 'var(--ink-2)' }}>{s.rotulo}</span>
            </span>
            <Odometro valor={valor} unidade="kWh/mês" />
            <span className="dl">
              {valor === null
                ? 'Sem dado neste ano'
                : semDado(c.variacao_kwh)
                  ? `${umaCasa(valor)} kWh/mês por pessoa`
                  : `${comSinal(c.variacao_kwh)} kWh desde 2026 (${comSinal(c.variacao_pct)}%)`}
            </span>
          </div>
        )
      })}
      <div className="cmp" data-testid="decomposicao">
        {[
          ['Efeito do envelhecimento (taxas menos contrafactual)', 'efeito_envelhecimento'],
          ['Efeito da idade (arranjos fixos menos contrafactual)', 'efeito_idade'],
          ['Efeito dos arranjos (taxas menos arranjos fixos)', 'efeito_arranjos'],
        ].map(([rotulo, campo]) => (
          <div key={campo}>
            <span>{rotulo}</span>
            <b className="num">
              {semDado(ponto?.[`${campo}_kwh`]) ? 'sem dado' : `${comSinal(ponto[`${campo}_kwh`])} kWh`}
              {!semDado(ponto?.[`${campo}_total_kwh_mes`]) && (
                <small>
                  {' '}
                  ({sinal(ponto[`${campo}_total_kwh_mes`])}
                  {milhoes(Math.abs(ponto[`${campo}_total_kwh_mes`]))} de kWh/mês)
                </small>
              )}
            </b>
          </div>
        ))}
        <div>
          <span>Consumo total do recorte, método das taxas (kWh/mês)</span>
          <b className="num">{semDado(taxas?.consumo_total_calibrado_kwh_mes) ? 'sem dado' : milhoes(taxas.consumo_total_calibrado_kwh_mes)}</b>
        </div>
        <div>
          <span>Participação 60+ na população</span>
          <b className="num">{semDado(ponto?.participacao_60_mais_pct) ? 'sem dado' : `${umaCasa(ponto.participacao_60_mais_pct)}%`}</b>
        </div>
      </div>
    </div>
  )
}
