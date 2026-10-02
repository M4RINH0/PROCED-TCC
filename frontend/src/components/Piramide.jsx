import { useTamanho } from '../hooks/useTamanho.js'
import { umaCasa } from '../utils/formato.js'

const FAIXAS_60 = new Set(['60 a 69', '70 a 79', '80+'])

/* Pirâmide do protótipo: barras do ano e o contorno tracejado de 2026.
   faixas e contorno: [{ faixa, homens_pct, mulheres_pct }] da mais nova para a mais velha */
export default function Piramide({ faixas, contorno }) {
  const [ref, { largura: W, altura: H }] = useTamanho({ largura: 520, altura: 400 })
  const mob = W < 520
  const m = { t: 26, r: 8, b: 22, l: 8 }
  const gap = mob ? 44 : 56
  const n = faixas.length
  const bh = (H - m.t - m.b) / n
  const meia = (W - m.l - m.r - gap) / 2
  const maximo = Math.max(8, ...faixas.flatMap((f) => [f.homens_pct, f.mulheres_pct]), ...contorno.flatMap((f) => [f.homens_pct, f.mulheres_pct]))
  const cl = m.l + meia
  const cr = cl + gap
  const larg = (pct) => (pct / maximo) * meia
  const passo = mob ? 4 : 2
  const marcas = []
  for (let p = 0; p <= maximo; p += passo) marcas.push(p)

  return (
    <div className="plot" ref={ref}>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Pirâmide etária do ano selecionado, com o contorno de 2026">
        <text className="psex" x={cl - 6} y={m.t - 10} textAnchor="end">
          Homens
        </text>
        <text className="psex" x={cr + 6} y={m.t - 10}>
          Mulheres
        </text>
        {marcas.map((p) => (
          <g key={p}>
            <line className="gl" x1={cl - larg(p)} x2={cl - larg(p)} y1={m.t - 4} y2={H - m.b} />
            <line className="gl" x1={cr + larg(p)} x2={cr + larg(p)} y1={m.t - 4} y2={H - m.b} />
            <text className="ax-s" x={cl - larg(p)} y={H - 6} textAnchor="middle">
              {p}%
            </text>
            <text className="ax-s" x={cr + larg(p)} y={H - 6} textAnchor="middle">
              {p}%
            </text>
          </g>
        ))}
        {[...faixas].reverse().map((f, i) => {
          const y = m.t + i * bh + 2
          const h = Math.max(6, bh - 5)
          const classe = FAIXAS_60.has(f.faixa) ? 'p60' : 'plo'
          const c26 = contorno.find((c) => c.faixa === f.faixa)
          return (
            <g key={f.faixa} data-testid={`faixa-${f.faixa}`}>
              <rect className={classe} x={(cl - larg(f.homens_pct)).toFixed(1)} y={y.toFixed(1)} width={larg(f.homens_pct).toFixed(1)} height={h.toFixed(1)} rx="2">
                <title>{`Homens de ${f.faixa}: ${umaCasa(f.homens_pct)}%`}</title>
              </rect>
              <rect className={classe} x={cr} y={y.toFixed(1)} width={larg(f.mulheres_pct).toFixed(1)} height={h.toFixed(1)} rx="2">
                <title>{`Mulheres de ${f.faixa}: ${umaCasa(f.mulheres_pct)}%`}</title>
              </rect>
              {c26 && (
                <>
                  <rect className="pout" x={(cl - larg(c26.homens_pct)).toFixed(1)} y={(y - 1).toFixed(1)} width={larg(c26.homens_pct).toFixed(1)} height={(h + 2).toFixed(1)} rx="2" />
                  <rect className="pout" x={cr} y={(y - 1).toFixed(1)} width={larg(c26.mulheres_pct).toFixed(1)} height={(h + 2).toFixed(1)} rx="2" />
                </>
              )}
              <text className={FAIXAS_60.has(f.faixa) ? 'plab on' : 'plab'} x={(cl + cr) / 2} y={(y + h / 2 + 4).toFixed(1)} textAnchor="middle">
                {f.faixa}
              </text>
            </g>
          )
        })}
      </svg>
    </div>
  )
}
