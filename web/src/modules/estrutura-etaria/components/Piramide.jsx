import { umaCasa } from '../../../shared/index.js'

const L = 520
const A = 320
const M = { t: 26, b: 24 }
const CENTRO = 64
const FAIXAS_60 = new Set(['60 a 69', '70 a 79', '80+'])

/* faixas: [{ faixa, homens_pct, mulheres_pct }] da mais nova para a mais velha */
export default function Piramide({ faixas }) {
  const maximo = Math.max(1, ...faixas.flatMap((f) => [f.homens_pct, f.mulheres_pct]))
  const meia = (L - CENTRO) / 2
  const altura = (A - M.t - M.b) / faixas.length
  const esquerda = meia
  const direita = meia + CENTRO
  const largura = (pct) => (pct / maximo) * (meia - 8)
  const ordem = [...faixas].reverse()

  return (
    <svg className="grafico" viewBox={`0 0 ${L} ${A}`} role="img" aria-label="Pirâmide etária do Brasil no ano selecionado">
      <text className="psex" x={esquerda - 4} y={M.t - 10} textAnchor="end">
        Homens
      </text>
      <text className="psex" x={direita + 4} y={M.t - 10}>
        Mulheres
      </text>
      {ordem.map((f, i) => {
        const y = M.t + i * altura + 2
        const h = Math.max(4, altura - 5)
        const classe = FAIXAS_60.has(f.faixa) ? 'p60' : 'plo'
        return (
          <g key={f.faixa} data-testid={`faixa-${f.faixa}`}>
            <rect className={classe} x={esquerda - largura(f.homens_pct)} y={y} width={largura(f.homens_pct)} height={h} rx="2">
              <title>{`Homens de ${f.faixa}: ${umaCasa(f.homens_pct)}%`}</title>
            </rect>
            <rect className={classe} x={direita} y={y} width={largura(f.mulheres_pct)} height={h} rx="2">
              <title>{`Mulheres de ${f.faixa}: ${umaCasa(f.mulheres_pct)}%`}</title>
            </rect>
            <text className={FAIXAS_60.has(f.faixa) ? 'plab on' : 'plab'} x={L / 2} y={y + h / 2 + 4} textAnchor="middle">
              {f.faixa}
            </text>
          </g>
        )
      })}
    </svg>
  )
}
