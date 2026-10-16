import { useTamanho } from '../hooks/useTamanho.js'
import { umaCasa } from '../utils/formato.js'

const FAIXAS_60 = new Set(['60 a 69', '70 a 79', '80+'])

/* Consumo por pessoa em cada faixa do chefe. Barras começam no zero. */
export default function BarrasFaixa({ faixas }) {
  const [ref, { largura: W, altura: H }] = useTamanho({ largura: 520, altura: 240 })
  const m = { t: 24, r: 12, b: 28, l: 40 }
  const iw = W - m.l - m.r
  const ih = H - m.t - m.b
  const valores = faixas.map((f) => f.consumo_per_capita_kwh ?? 0)
  const topo = Math.max(20, Math.ceil((Math.max(...valores) * 1.1) / 20) * 20)
  const marcas = []
  for (let v = 0; v <= topo; v += topo <= 100 ? 20 : 50) marcas.push(v)
  const largura = iw / faixas.length
  const bw = Math.min(46, largura * 0.62)
  const y = (v) => m.t + ih - (v / topo) * ih

  return (
    <div className="plot plot-barras" ref={ref}>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Consumo por pessoa por faixa etária do chefe do domicílio">
        {marcas.map((v) => (
          <g key={v}>
            <line className="gl" x1={m.l} x2={m.l + iw} y1={y(v)} y2={y(v)} />
            <text className="ax" x={m.l - 7} y={y(v) + 4} textAnchor="end">
              {v}
            </text>
          </g>
        ))}
        <line className="bl" x1={m.l} x2={m.l + iw} y1={y(0)} y2={y(0)} />
        {faixas.map((f, i) => {
          const cx = m.l + i * largura + largura / 2
          const v = f.consumo_per_capita_kwh
          return (
            <g key={f.faixa} data-testid={`barra-${f.faixa}`}>
              {v !== null && (
                <>
                  <rect className={FAIXAS_60.has(f.faixa) ? 'hb2 last' : 'hb2'} x={cx - bw / 2} y={y(v)} width={bw} height={y(0) - y(v)} rx="3" />
                  <text className="hval" x={cx} y={y(v) - 5} textAnchor="middle">
                    {umaCasa(v)}
                  </text>
                </>
              )}
              <text className="hlab" x={cx} y={H - 9} textAnchor="middle">
                {f.faixa}
              </text>
            </g>
          )
        })}
      </svg>
    </div>
  )
}
