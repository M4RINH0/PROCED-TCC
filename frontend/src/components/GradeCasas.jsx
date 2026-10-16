import { useTamanho } from '../hooks/useTamanho.js'
import { APARENCIA, noFiltro } from '../utils/categorias.js'
import { melhorGrade } from '../utils/grade.js'
import { CAMINHO_CASA } from './Icone.jsx'

/* Isotype do protótipo: 100 casas coloridas por arranjo, preenchidas por linha (os arranjos do recorte
   ficam nas primeiras casas). casas[i] = quantidade da categoria i */
export default function GradeCasas({ categorias, casas, filtro, destaque }) {
  const [ref, { largura: W, altura: H }] = useTamanho({ largura: 520, altura: 420 })
  // as colunas acompanham a forma do painel, para a grade ocupá-lo inteiro
  const { colunas, linhas, celula, gap } = melhorGrade(W, H)
  const escala = celula / 20
  const ox = (W - (celula * colunas + gap * (colunas - 1))) / 2
  const oy = (H - (celula * linhas + gap * (linhas - 1))) / 2

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
