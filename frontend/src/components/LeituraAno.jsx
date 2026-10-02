import { comSinal, umaCasa } from '../utils/formato.js'
import { SERIES } from '../utils/series.js'
import Odometro from './Odometro.jsx'

export function textoSemValor(modelado) {
  if (!modelado) return 'Cenário ainda não modelado'
  return 'Sem dado neste ano'
}

/* Painel "Leitura do ano" do protótipo. ponto: item da série no ano; modelados: ids com valor em algum ano */
export default function LeituraAno({ ponto, ano, modelados, visiveis }) {
  const cenario = (id) => ponto?.cenarios.find((c) => c.id === id)
  const texto = (v, sufixo) => (v === null || v === undefined ? 'sem dado' : `${v}${sufixo}`)
  return (
    <div className="readout">
      <div className="ro-h">
        <h2 id="h-ro">Leitura do ano</h2>
        <span className="yr num">{ano}</span>
      </div>
      {SERIES.map((s) => {
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
                ? textoSemValor(modelados.includes(s.id))
                : c.variacao_kwh === null || c.variacao_kwh === undefined
                  ? `${umaCasa(valor)} kWh/mês por pessoa`
                  : `${comSinal(c.variacao_kwh)} kWh desde 2026 (${comSinal(c.variacao_pct)}%)`}
            </span>
          </div>
        )
      })}
      <div className="cmp">
        <div>
          <span>Amplitude entre cenários</span>
          <b className="num">{ponto?.amplitude_kwh == null ? 'sem dado' : `${umaCasa(ponto.amplitude_kwh)} kWh`}</b>
        </div>
        <div>
          <span>Modelo menos oficial</span>
          <b className="num">{ponto?.modelo_menos_oficial_kwh == null ? 'sem dado' : `${comSinal(ponto.modelo_menos_oficial_kwh)} kWh`}</b>
        </div>
        <div>
          <span>Participação 60+ na população</span>
          <b className="num">{texto(ponto?.participacao_60_mais_pct == null ? null : umaCasa(ponto.participacao_60_mais_pct), '%')}</b>
        </div>
      </div>
    </div>
  )
}
