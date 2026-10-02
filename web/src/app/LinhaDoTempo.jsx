import { useEffect, useRef, useState } from 'react'
import { Icone } from '../shared/index.js'

export const ANO_INICIAL = 2026
export const ANO_FINAL = 2075
export const ANO_FINAL_IBGE = 2070
const ANOS_POR_SEGUNDO = 9
const MARCAS = [
  [2026, 's'],
  [2035, 'm'],
  [2045, 'm'],
  [2070, 'b'],
  [2075, 'e'],
]

export const posicao = (ano) => ((ano - ANO_INICIAL) / (ANO_FINAL - ANO_INICIAL)) * 100

const reduzMovimento = () => globalThis.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false

/* Linha do tempo flutuante do protótipo: controla o ano de Panorama, Domicílios e Estrutura etária */
export default function LinhaDoTempo({ ano, aoMudarAno, oculta }) {
  const [tocando, setTocando] = useState(false)
  const quadro = useRef(0)
  const anoRef = useRef(ano)
  anoRef.current = ano

  const parar = () => {
    cancelAnimationFrame(quadro.current)
    setTocando(false)
    aoMudarAno(Math.round(anoRef.current))
  }

  const tocar = () => {
    if (reduzMovimento()) {
      aoMudarAno(ANO_FINAL)
      return
    }
    let atual = anoRef.current >= ANO_FINAL - 0.01 ? ANO_INICIAL : anoRef.current
    let ultimo = performance.now()
    setTocando(true)
    const passo = (agora) => {
      const dt = Math.min(64, agora - ultimo)
      ultimo = agora
      atual += (dt / 1000) * ANOS_POR_SEGUNDO
      if (atual >= ANO_FINAL) {
        aoMudarAno(ANO_FINAL)
        setTocando(false)
        return
      }
      aoMudarAno(atual)
      quadro.current = requestAnimationFrame(passo)
    }
    quadro.current = requestAnimationFrame(passo)
  }

  useEffect(() => () => cancelAnimationFrame(quadro.current), [])
  useEffect(() => {
    if (oculta && tocando) parar()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [oculta])

  const inteiro = Math.round(ano)
  return (
    <div className={oculta ? 'dock hide' : 'dock'} role="group" aria-label="Linha do tempo" aria-hidden={oculta}>
      <button type="button" className="play" aria-label={tocando ? 'Pausar' : 'Reproduzir os 50 anos'} onClick={tocando ? parar : tocar}>
        <Icone nome={tocando ? 'pause' : 'play'} />
      </button>
      <div className="dyear">
        <small>Ano</small>
        <b className="num">{inteiro}</b>
      </div>
      <div className="tl">
        <div className="tl-track">
          <div className="tl-fill" style={{ width: `${posicao(ano)}%` }} />
          <div className="tl-off" style={{ '--bp': `${posicao(ANO_FINAL_IBGE).toFixed(2)}%` }} title={`Sem projeção oficial após ${ANO_FINAL_IBGE}`} />
        </div>
        <input
          type="range"
          min={ANO_INICIAL}
          max={ANO_FINAL}
          step="1"
          value={inteiro}
          aria-label="Ano da projeção"
          aria-valuetext={String(inteiro)}
          onChange={(e) => {
            if (tocando) parar()
            aoMudarAno(Number(e.target.value))
          }}
        />
        <div className="tl-ticks">
          {MARCAS.map(([a, c]) => (
            <span key={a} className={c} style={{ left: `${posicao(a)}%` }}>
              {a}
            </span>
          ))}
        </div>
      </div>
      <div className="dnote">Hachura: sem projeção oficial após {ANO_FINAL_IBGE}</div>
    </div>
  )
}
