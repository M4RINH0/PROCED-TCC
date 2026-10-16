import { useTamanho } from '../hooks/useTamanho.js'
import { escalaY, estiloDoGrupo } from '../utils/comparacao.js'
import { compacto } from '../utils/formato.js'
import { afastarRotulos } from './GraficoSerie.jsx'

const INICIO = 2026
const FIM = 2070
const ALTURA_ROTULO = 30 // nome e valor no fim da linha

/* Uma linha por grupo de 2026 a 2070 (RF12). Cor pelo arranjo, traço pela idade e rótulo direto no
   fim de cada linha; no celular, os rótulos viram uma legenda com a mesma amostra de traço.
   grupos: os de /comparacao, com pontos [{ ano, valor }]; forma: indice ou absoluto. */
export default function GraficoComparacao({ grupos, forma, unidade }) {
  const [ref, { largura: W, altura: H }] = useTamanho({ largura: 800, altura: 380 })
  const mob = W < 560
  const m = { t: 22, r: mob ? 14 : 190, b: 30, l: 58 }
  const iw = Math.max(10, W - m.l - m.r)
  const ih = Math.max(10, H - m.t - m.b)
  const comValor = grupos.filter((g) => g.pontos.some((p) => p.valor !== null))
  const valores = comValor.flatMap((g) => g.pontos.map((p) => p.valor))
  const { lo, hi, marcas } = escalaY(forma === 'indice' ? [...valores, 100] : valores, mob ? 4 : 5)
  const x = (a) => m.l + ((a - INICIO) / (FIM - INICIO)) * iw
  const y = (v) => m.t + ih - ((v - lo) / (hi - lo || 1)) * ih
  const caminho = (pontos) =>
    pontos
      .filter((p) => p.valor !== null)
      .map((p, i) => `${i ? 'L' : 'M'}${x(p.ano).toFixed(1)},${y(p.valor).toFixed(1)}`)
      .join('')
  const ultimo = (g) => [...g.pontos].reverse().find((p) => p.valor !== null)
  const posicoes = Object.fromEntries(
    afastarRotulos(
      comValor.map((g) => ({ id: g.id, y: y(ultimo(g).valor) - 4 })),
      ALTURA_ROTULO,
      m.t + 4,
      m.t + ih - ALTURA_ROTULO + 8,
    ).map((a) => [a.id, a.y]),
  )
  const formatar = (v) => (forma === 'indice' ? v.toLocaleString('pt-BR', { maximumFractionDigits: 1 }) : compacto(v))
  const descricao = `${forma === 'indice' ? 'Índice com 2026 = 100' : unidade} de ${comValor.map((g) => g.rotulo).join(', ')}, de ${INICIO} a ${FIM}`

  return (
    <>
      {mob && (
        <ul className="cmp-leg" aria-hidden="true">
          {comValor.map((g) => {
            const e = estiloDoGrupo(g.id)
            return (
              <li key={g.id}>
                <svg width="26" height="10">
                  <line x1="1" x2="25" y1="5" y2="5" stroke={e.cor} strokeWidth={e.espessura} strokeDasharray={e.tracejado} />
                </svg>
                {g.rotulo}
              </li>
            )
          })}
        </ul>
      )}
      <div className="plot plot-cmp" ref={ref}>
        <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={descricao}>
          {marcas.map((v) => (
            <g key={v}>
              <line className="gl" x1={m.l} x2={m.l + iw} y1={y(v)} y2={y(v)} />
              <text className="ax num" x={m.l - 8} y={y(v) + 4} textAnchor="end">
                {formatar(v)}
              </text>
            </g>
          ))}
          {forma === 'indice' && <line className="guia" x1={m.l} x2={m.l + iw} y1={y(100)} y2={y(100)} data-testid="base-100" />}
          {(mob ? [INICIO, 2050, FIM] : [INICIO, 2035, 2045, 2055, FIM]).map((a) => (
            <text key={a} className="ax num" x={x(a)} y={H - 9} textAnchor={a === INICIO ? 'start' : a === FIM ? 'end' : 'middle'}>
              {a}
            </text>
          ))}
          {comValor.map((g) => {
            const e = estiloDoGrupo(g.id)
            return (
              <path
                key={g.id}
                data-testid={`linha-cmp-${g.id}`}
                d={caminho(g.pontos)}
                fill="none"
                stroke={e.cor}
                strokeWidth={e.espessura}
                strokeDasharray={e.tracejado}
                strokeLinejoin="round"
                strokeLinecap="round"
              />
            )
          })}
          {!mob &&
            comValor.map((g) => {
              const e = estiloDoGrupo(g.id)
              const fim = ultimo(g)
              return (
                <g key={g.id} data-testid={`rotulo-cmp-${g.id}`}>
                  <text className="cmp-rot" x={x(FIM) + 10} y={posicoes[g.id]} fill={e.cor}>
                    {g.rotulo}
                  </text>
                  <text className="cmp-val num" x={x(FIM) + 10} y={posicoes[g.id] + 14}>
                    {formatar(fim.valor)} em {fim.ano}
                  </text>
                </g>
              )
            })}
        </svg>
      </div>
    </>
  )
}
