import { umaCasa } from '../utils/formato.js'

/* Medidor do protótipo: dígitos que rolam (só transform). Formato 000,0.
   Os dígitos são decorativos; o valor vai em texto para leitores de tela. */
const DIGITOS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

export function digitos(valor) {
  const t = Math.round(Math.max(0, Math.min(999.9, valor)) * 10)
  return [Math.floor(t / 1000) % 10, Math.floor(t / 100) % 10, Math.floor(t / 10) % 10, t % 10]
}

function Coluna({ digito, apagado }) {
  return (
    <span className={apagado ? 'dg lz' : 'dg'}>
      <span className="st" style={{ transform: `translateY(${-digito}em)` }}>
        {DIGITOS.map((d) => (
          <span key={d}>{d}</span>
        ))}
      </span>
    </span>
  )
}

export default function Odometro({ valor, unidade }) {
  if (valor === null || valor === undefined) {
    return (
      <>
        <span className="odo off" aria-hidden="true" />
        <span className="sr">sem dado</span>
      </>
    )
  }
  const [c, d, u, dec] = digitos(valor)
  return (
    <>
    <span className="sr">{`${umaCasa(valor)} ${unidade ?? ''}`.trim()}</span>
    <span className="odo" aria-hidden="true">
      <Coluna digito={c} apagado={c === 0} />
      <Coluna digito={d} apagado={c === 0 && d === 0} />
      <Coluna digito={u} />
      <span className="sep">,</span>
      <Coluna digito={dec} />
      {unidade && <span className="u">{unidade}</span>}
    </span>
    </>
  )
}
