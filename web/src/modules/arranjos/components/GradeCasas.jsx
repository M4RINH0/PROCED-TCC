import { CAMINHO_CASA, useTamanho } from '../../../shared/index.js'
import { APARENCIA, noFiltro } from '../categorias.js'

/* Isotype do protótipo: 100 casas coloridas por arranjo. casas[i] = quantidade da categoria i */
export default function GradeCasas({ categorias, casas, filtro, destaque }) {
  const [ref, { largura: W, altura: H }] = useTamanho({ largura: 520, altura: 420 })
  const colunas = 10
  const gap = Math.max(3, Math.min(W, H) * 0.012)
  const celula = Math.min((W - gap * (colunas - 1)) / colunas, (H - gap * (colunas - 1)) / colunas)
  const escala = celula / 20
  const ox = (W - (celula * colunas + gap * (colunas - 1))) / 2
  const oy = (H - (celula * colunas + gap * (colunas - 1))) / 2

  const lista = []
  categorias.forEach((c, i) => {
    for (let j = 0; j < (casas[i] ?? 0); j++) lista.push(c)
  })

  return (
    <div className={destaque ? 'iso hovering' : 'iso'} ref={ref}>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Cem domicílios, coloridos por arranjo domiciliar">
        {lista.slice(0, 100).map((c, i) => {
          const col = i % colunas
          const lin = Math.floor(i / colunas)
          const classes = ['hs', APARENCIA[c.id].classe]
          if (!noFiltro(c, filtro)) classes.push('dim')
          if (destaque === c.id) classes.push('hl')
          return (
            <path
              key={i}
              className={classes.join(' ')}
              data-categoria={c.id}
              fillRule="evenodd"
              d={CAMINHO_CASA}
              transform={`translate(${(ox + col * (celula + gap)).toFixed(1)},${(oy + lin * (celula + gap)).toFixed(1)}) scale(${escala.toFixed(3)})`}
            />
          )
        })}
      </svg>
    </div>
  )
}
