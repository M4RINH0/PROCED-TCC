import { useEffect, useRef, useState } from 'react'
import { Icone } from '../shared/index.js'

/* Menu do protótipo para apresentar os estados de falha e de carregamento */
export default function MenuDemonstracao({ falha, aoAlternarFalha, aoReverCarregamento }) {
  const [aberto, setAberto] = useState(false)
  const raiz = useRef(null)

  useEffect(() => {
    if (!aberto) return undefined
    const fora = (e) => raiz.current && !raiz.current.contains(e.target) && setAberto(false)
    const esc = (e) => e.key === 'Escape' && setAberto(false)
    document.addEventListener('click', fora)
    document.addEventListener('keydown', esc)
    return () => {
      document.removeEventListener('click', fora)
      document.removeEventListener('keydown', esc)
    }
  }, [aberto])

  return (
    <div className="demo" ref={raiz}>
      <button
        type="button"
        className={falha ? 'ib failing' : 'ib'}
        aria-haspopup="true"
        aria-expanded={aberto}
        aria-controls="demoPop"
        onClick={() => setAberto((a) => !a)}
      >
        <Icone nome="flask" />
        <span>Demonstração</span>
      </button>
      {aberto && (
        <div className="demopop" id="demoPop">
          <p className="dp-t">Modo demonstração</p>
          <button type="button" className="dp-row" role="switch" aria-checked={falha} onClick={aoAlternarFalha}>
            <span>
              <b>Simular falha de conexão</b>
              <small>A API deixa de responder. As telas mostram o erro e preservam os parâmetros.</small>
            </span>
            <i className="tog" aria-hidden="true" />
          </button>
          <button
            type="button"
            className="dp-row"
            onClick={() => {
              setAberto(false)
              aoReverCarregamento()
            }}
          >
            <span>
              <b>Rever carregamento</b>
              <small>Mostra de novo o estado de carregamento da tela atual.</small>
            </span>
          </button>
        </div>
      )}
    </div>
  )
}
