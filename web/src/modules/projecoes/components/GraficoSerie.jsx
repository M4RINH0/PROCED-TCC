import { umaCasa } from '../../../shared/index.js'
import { ANO_FINAL, ANO_FINAL_IBGE, ANO_INICIAL, SERIES } from '../series.js'

const L = 1200
const A = 380
const M = { t: 30, r: 190, b: 30, l: 48 }

/* Escala do eixo: começa no zero para não exagerar variações pequenas */
export function dominioY(series) {
  const valores = series.flatMap((s) => s.pontos.map((p) => p.valor)).filter((v) => v !== null)
  if (!valores.length) return [0, 100]
  const passo = 20
  return [0, Math.ceil((Math.max(...valores) * 1.15) / passo) * passo]
}

export function marcasY([, max]) {
  const passo = max <= 160 ? 20 : max <= 400 ? 50 : 100
  const marcas = []
  for (let v = 0; v <= max; v += passo) marcas.push(v)
  return marcas
}

/* series: [{ id, pontos: [{ ano, valor }] }] */
export default function GraficoSerie({ series, anoSelecionado }) {
  const iw = L - M.l - M.r
  const ih = A - M.t - M.b
  const [, ymax] = dominioY(series)
  const x = (ano) => M.l + ((ano - ANO_INICIAL) / (ANO_FINAL - ANO_INICIAL)) * iw
  const y = (v) => M.t + ih - (v / ymax) * ih
  const caminho = (pontos) =>
    pontos
      .filter((p) => p.valor !== null)
      .map((p, i) => `${i ? 'L' : 'M'}${x(p.ano).toFixed(1)},${y(p.valor).toFixed(1)}`)
      .join('')

  return (
    <svg
      className="grafico"
      viewBox={`0 0 ${L} ${A}`}
      role="img"
      aria-label={`Consumo residencial per capita projetado, ${ANO_INICIAL} a ${ANO_FINAL}`}
    >
      <defs>
        <pattern id="hachura" width="8" height="8" patternTransform="rotate(45)" patternUnits="userSpaceOnUse">
          <rect className="hatch-bg" width="8" height="8" />
          <line className="hatch-l" x1="0" y1="0" x2="0" y2="8" />
        </pattern>
      </defs>
      <rect fill="url(#hachura)" x={x(ANO_FINAL_IBGE)} y={M.t} width={M.l + iw - x(ANO_FINAL_IBGE)} height={ih} />
      {marcasY([0, ymax]).map((v) => (
        <g key={v}>
          <line className="gl" x1={M.l} x2={M.l + iw} y1={y(v)} y2={y(v)} />
          <text className="ax" x={M.l - 8} y={y(v) + 4} textAnchor="end">
            {v}
          </text>
        </g>
      ))}
      {[2026, 2035, 2045, 2055, 2070, 2075].map((a) => (
        <text key={a} className="ax" x={x(a)} y={A - 9} textAnchor={a === ANO_INICIAL ? 'start' : a === ANO_FINAL ? 'end' : 'middle'}>
          {a}
        </text>
      ))}
      <line className="b60" x1={x(ANO_FINAL_IBGE)} x2={x(ANO_FINAL_IBGE)} y1={M.t - 6} y2={M.t + ih} />
      <text className="b60t" x={x(ANO_FINAL_IBGE) - 6} y={M.t - 10} textAnchor="end">
        Sem projeção oficial após {ANO_FINAL_IBGE}
      </text>
      {series.map((s) => {
        const validos = s.pontos.filter((p) => p.valor !== null)
        if (validos.length < 2) return null
        const ultimo = validos[validos.length - 1]
        const rotulo = SERIES.find((r) => r.id === s.id)?.rotulo
        return (
          <g key={s.id} data-testid={`linha-${s.id}`}>
            <path className={`ln s-${s.id}`} d={caminho(s.pontos)} />
            <text className={`endl t-${s.id}-txt`} x={x(ultimo.ano) + 8} y={y(ultimo.valor) + 4}>
              {rotulo}
            </text>
            <text className="endv" x={x(ultimo.ano) + 8} y={y(ultimo.valor) + 18}>
              {umaCasa(ultimo.valor)} em {ultimo.ano}
            </text>
          </g>
        )
      })}
      <line className="cur" x1={x(anoSelecionado)} x2={x(anoSelecionado)} y1={M.t} y2={M.t + ih} />
    </svg>
  )
}
