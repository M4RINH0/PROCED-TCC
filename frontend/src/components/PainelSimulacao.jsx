import { useId } from 'react'
import { CONTROLES, PADRAO_SIMULACAO, lerControle } from '../utils/simulacao.js'
import { umaCasa } from '../utils/formato.js'

/* Painel "Parâmetros de simulação" (RF02), igual em todas as páginas.
   simulacao: estado global do App; semEfeito: { k?: frase, intensidade?: frase } para o que a página não usa */
export default function PainelSimulacao({ simulacao, semEfeito = {} }) {
  const id = useId()
  const { valores, ativa, aoMudar, restaurar } = simulacao
  return (
    <section className="sim-painel" aria-labelledby={`${id}-t`}>
      <div className="sim-h">
        <span className="flab" id={`${id}-t`}>
          Parâmetros de simulação
        </span>
        {ativa && (
          <>
            <span className="chip-sim" data-testid="rotulo-simulacao">
              Simulação
            </span>
            <button type="button" className="lnk" onClick={restaurar}>
              Restaurar padrão
            </button>
          </>
        )}
      </div>
      <div className="sim-ctrls">
        {Object.entries(CONTROLES).map(([campo, c]) => {
          const valor = valores[campo]
          const motivo = semEfeito[campo]
          const padrao = valor === PADRAO_SIMULACAO[campo]
          return (
            <div className="fl" key={campo}>
              <div className="rangeh">
                <label htmlFor={`${id}-${campo}`}>{c.rotulo}</label>
                <output htmlFor={`${id}-${campo}`}>
                  {umaCasa(valor)}
                  {padrao && <small> ({c.padrao})</small>}
                </output>
              </div>
              <input
                className="tx"
                type="range"
                id={`${id}-${campo}`}
                min={c.min}
                max={c.max}
                step={c.passo}
                value={valor}
                disabled={Boolean(motivo)}
                aria-describedby={`${id}-${campo}-ajuda`}
                onChange={(e) => aoMudar(campo, lerControle(e.target.value))}
              />
              <div className="help" id={`${id}-${campo}-ajuda`}>
                {motivo ?? c.ajuda}
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
