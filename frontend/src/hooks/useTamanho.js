import { useEffect, useRef, useState } from 'react'

/* Mede o elemento para desenhar o SVG no tamanho real, como no protótipo:
   o texto do gráfico fica do mesmo tamanho do resto da interface. */
export function useTamanho(padrao = { largura: 800, altura: 380 }) {
  const ref = useRef(null)
  const [tamanho, setTamanho] = useState(padrao)

  useEffect(() => {
    const el = ref.current
    if (!el) return undefined
    const medir = () => {
      const r = el.getBoundingClientRect()
      if (r.width > 0 && r.height > 0) {
        setTamanho({ largura: Math.max(240, Math.floor(r.width)), altura: Math.max(150, Math.floor(r.height)) })
      }
    }
    medir()
    if (typeof ResizeObserver === 'undefined') return undefined
    const observador = new ResizeObserver(medir)
    observador.observe(el)
    return () => observador.disconnect()
  }, [])

  return [ref, tamanho]
}
