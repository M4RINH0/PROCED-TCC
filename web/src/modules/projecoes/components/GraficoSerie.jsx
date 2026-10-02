import { useId, useRef, useState } from 'react'
import { umaCasa, useTamanho } from '../../../shared/index.js'
import { ANO_FINAL, ANO_FINAL_IBGE, ANO_INICIAL, SERIES } from '../series.js'

/* Faixa do eixo como no protótipo: folga de 6 kWh e múltiplos de 20 */
export function dominioY(series) {
  const valores = series.flatMap((s) => s.pontos.map((p) => p.valor)).filter((v) => v !== null)
  if (!valores.length) return [120, 280]
  return [Math.floor((Math.min(...valores) - 6) / 20) * 20, Math.ceil((Math.max(...valores) + 6) / 20) * 20]
}

export function marcasY([lo, hi], quantidade = 5) {
  const bruto = (hi - lo) / Math.max(1, quantidade)
  const passo = [5, 10, 20, 25, 40, 50, 100].find((p) => p >= bruto) || 100
  const marcas = []
  for (let v = Math.ceil(lo / passo) * passo; v <= hi + 1e-6; v += passo) marcas.push(v)
  return marcas
}

const caminho = (pontos, x, y) =>
  pontos
    .filter((p) => p.valor !== null)
    .map((p, i) => `${i ? 'L' : 'M'}${x(p.ano).toFixed(1)},${y(p.valor).toFixed(1)}`)
    .join('')

/* series: [{ id, pontos: [{ ano, valor }] }]; visiveis: { id: bool } */
export default function GraficoSerie({ series, visiveis, ano, aoMudarAno }) {
  const [ref, { largura: W, altura: H }] = useTamanho({ largura: 800, altura: 380 })
  const idClip = useId().replace(/:/g, '')
  const [dica, setDica] = useState(null)
  const arrastando = useRef(false)

  const mob = W < 560
  const m = { t: 30, r: mob ? 14 : 140, b: 30, l: 44 }
  const iw = W - m.l - m.r
  const ih = H - m.t - m.b
  const ativas = series.filter((s) => visiveis[s.id])
  const [lo, hi] = dominioY(ativas)
  const x = (a) => m.l + ((a - ANO_INICIAL) / (ANO_FINAL - ANO_INICIAL)) * iw
  const y = (v) => m.t + ih - ((v - lo) / (hi - lo)) * ih
  const meta = (id) => SERIES.find((s) => s.id === id)

  /* faixa entre cenários: envelope dos visíveis com dado */
  const topo = []
  const base = []
  for (let a = ANO_INICIAL; a <= ANO_FINAL; a++) {
    const vs = ativas.map((s) => s.pontos.find((p) => p.ano === a)?.valor).filter((v) => v !== null && v !== undefined)
    if (vs.length > 1) {
      topo.push({ ano: a, valor: Math.max(...vs) })
      base.push({ ano: a, valor: Math.min(...vs) })
    }
  }

  const anoDoPonteiro = (ev) => {
    const r = ev.currentTarget.ownerSVGElement.getBoundingClientRect()
    const px = ((ev.clientX - r.left) * W) / (r.width || W)
    return Math.max(ANO_INICIAL, Math.min(ANO_FINAL, Math.round(ANO_INICIAL + ((px - m.l) / iw) * (ANO_FINAL - ANO_INICIAL))))
  }
  const mostrarDica = (ev) => {
    const a = anoDoPonteiro(ev)
    const r = ev.currentTarget.ownerSVGElement.getBoundingClientRect()
    setDica({ ano: a, topo: Math.max(8, Math.min(ev.clientY - r.top - 60, H - 150)) })
    if (arrastando.current) aoMudarAno(a)
  }
  const teclado = (e) => {
    const passo = e.shiftKey ? 5 : 1
    const atual = Math.round(ano)
    const novo = { ArrowRight: atual + passo, ArrowLeft: atual - passo, Home: ANO_INICIAL, End: ANO_FINAL }[e.key]
    if (novo !== undefined) {
      e.preventDefault()
      aoMudarAno(Math.max(ANO_INICIAL, Math.min(ANO_FINAL, novo)))
    }
  }

  const xc = x(ano)
  const dx = Math.max(m.l + 22, Math.min(xc, W - 24)) - xc
  const anosEixo = mob ? [2026, 2050, 2075] : [2026, 2035, 2045, 2055, 2070, 2075]

  return (
    <div className="plot" ref={ref} tabIndex={0} onKeyDown={teclado} aria-label="Gráfico da projeção. Use as setas para mudar o ano.">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Consumo residencial per capita projetado, ${ANO_INICIAL} a ${ANO_FINAL}`}>
        <rect className="fut" x={x(ANO_FINAL_IBGE)} y={m.t} width={m.l + iw - x(ANO_FINAL_IBGE)} height={ih} />
        {marcasY([lo, hi], mob ? 4 : 5).map((v) => (
          <g key={v}>
            <line className="gl" x1={m.l} x2={m.l + iw} y1={y(v)} y2={y(v)} />
            <text className="ax" x={m.l - 8} y={y(v) + 4} textAnchor="end">
              {Math.round(v)}
            </text>
          </g>
        ))}
        {anosEixo.map((a) => (
          <text key={a} className="ax" x={x(a)} y={H - 9} textAnchor={a === ANO_INICIAL ? 'start' : a === ANO_FINAL ? 'end' : 'middle'}>
            {a}
          </text>
        ))}
        <line className="bl" x1={m.l} x2={m.l + iw} y1={m.t + ih} y2={m.t + ih} />
        <line className="b60" x1={x(ANO_FINAL_IBGE)} x2={x(ANO_FINAL_IBGE)} y1={m.t - 6} y2={m.t + ih} />
        <text className="b60t" x={x(ANO_FINAL_IBGE) - 8} y={m.t + 13} textAnchor="end">
          {mob ? 'sem oficial' : `Sem projeção oficial após ${ANO_FINAL_IBGE}`}
        </text>
        {topo.length > 1 && (
          <path
            className="band"
            d={`${caminho(topo, x, y)}L${[...base].reverse().map((p) => `${x(p.ano).toFixed(1)},${y(p.valor).toFixed(1)}`).join('L')}Z`}
          />
        )}
        {ativas.map((s) => (
          <path key={`f-${s.id}`} className={`ln fade s-${s.id}`} d={caminho(s.pontos, x, y)} />
        ))}
        <clipPath id={idClip}>
          <rect x={m.l - 4} y="0" width={Math.max(0, xc - m.l + 4)} height={H} />
        </clipPath>
        <g clipPath={`url(#${idClip})`}>
          {ativas.map((s) => (
            <path key={`p-${s.id}`} className={`ln s-${s.id}`} d={caminho(s.pontos, x, y)} data-testid={`linha-${s.id}`} />
          ))}
        </g>
        {!mob &&
          ativas.map((s) => {
            const validos = s.pontos.filter((p) => p.valor !== null)
            const ultimo = validos[validos.length - 1]
            if (!ultimo) return null
            return (
              <g key={`r-${s.id}`}>
                <text className={`endl t-${s.id}`} x={x(ultimo.ano) + 9} y={y(ultimo.valor) + 4}>
                  {meta(s.id).curto}
                </text>
                <text className="endv" x={x(ultimo.ano) + 9} y={y(ultimo.valor) + 18}>
                  {umaCasa(ultimo.valor)} em {ultimo.ano}
                </text>
              </g>
            )
          })}
        <g transform={`translate(${xc.toFixed(1)},0)`}>
          <line className="cur" y1={m.t - 2} y2={m.t + ih} />
          <rect className="curtag" x={-22 + dx} y={m.t - 24} width="44" height="19" rx="5" />
          <text className="curtx" x={dx} y={m.t - 10} textAnchor="middle">
            {Math.round(ano)}
          </text>
          {ativas.map((s) => {
            const v = s.pontos.find((p) => p.ano === Math.round(ano))?.valor
            return v === null || v === undefined ? null : (
              <circle key={s.id} className={`dot s-${s.id}`} cy={y(v).toFixed(1)} r="4.6" style={{ strokeDasharray: 'none' }} />
            )
          })}
        </g>
        {dica && <line className="hov" x1={x(dica.ano)} x2={x(dica.ano)} y1={m.t} y2={m.t + ih} />}
        <rect
          x={m.l}
          y={m.t}
          width={Math.max(0, iw)}
          height={Math.max(0, ih)}
          fill="transparent"
          style={{ cursor: 'pointer', touchAction: 'none' }}
          data-testid="area-grafico"
          onPointerMove={mostrarDica}
          onPointerDown={(ev) => {
            arrastando.current = true
            ev.currentTarget.setPointerCapture?.(ev.pointerId)
            aoMudarAno(anoDoPonteiro(ev))
          }}
          onPointerUp={() => (arrastando.current = false)}
          onPointerLeave={() => !arrastando.current && setDica(null)}
        />
      </svg>
      <div
        className={dica ? 'tip on' : 'tip'}
        style={dica ? { left: x(dica.ano) > W - 220 ? Math.max(4, x(dica.ano) - 206) : x(dica.ano) + 14, top: dica.topo } : undefined}
      >
        {dica && (
          <>
            <b>{dica.ano}</b>
            {ativas.map((s) => {
              const v = s.pontos.find((p) => p.ano === dica.ano)?.valor
              return (
                <div key={s.id} style={{ color: `var(--${meta(s.id).cor})` }}>
                  <i />
                  <span style={{ color: 'var(--paper)' }}>{meta(s.id).curto}</span>
                  {v === null || v === undefined ? <small>sem dado</small> : <em style={{ color: 'var(--paper)' }}>{umaCasa(v)}</em>}
                </div>
              )
            })}
            <span className="hint">Clique ou arraste para levar a linha do tempo até aqui</span>
          </>
        )}
      </div>
    </div>
  )
}
