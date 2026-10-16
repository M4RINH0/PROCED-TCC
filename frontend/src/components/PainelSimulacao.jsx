import { useId, useState } from 'react'
import { CONTROLES, PADRAO_SIMULACAO, lerControle } from '../utils/simulacao.js'
import { umaCasa } from '../utils/formato.js'
import Icone from './Icone.jsx'

/* Painel "Parâmetros de simulação" (RF02), igual em todas as páginas. Os dois controles ficam numa linha
   só, e o título recolhe o painel para dar altura aos gráficos; recolhido, mostra os valores em uso.
   simulacao: estado global do App (recolhido e alternarRecolhido valem para todas as páginas);
   semEfeito: { k?: frase, intensidade?: frase } para o que a página não usa */
export default function PainelSimulacao({ simulacao, semEfeito = {} }) {
  const id = useId()
  const [recolhidoLocal, setRecolhidoLocal] = useState(false)
  const { valores, ativa, aoMudar, restaurar } = simulacao
  const recolhido = simulacao.recolhido ?? recolhidoLocal
  const alternar = simulacao.alternarRecolhido ?? (() => setRecolhidoLocal((r) => !r))
  return (
    <section className={recolhido ? 'sim-painel recolhido' : 'sim-painel'} aria-labelledby={`${id}-t`}>
      <div className="sim-h">
        <button
          type="button"
          className="sim-alterna"
          id={`${id}-t`}
          aria-expanded={!recolhido}
          aria-controls={`${id}-ctrls`}
          onClick={alternar}
        >
          Parâmetros de simulação
          <Icone nome="chev" />
        </button>
        {recolhido && (
          <span className="sim-resumo num" data-testid="resumo-simulacao">
            Velocidade {umaCasa(valores.k)}, intensidade {umaCasa(valores.intensidade)}
          </span>
        )}
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
      <div className="sim-ctrls" id={`${id}-ctrls`} hidden={recolhido}>
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
                title={motivo ?? c.ajuda}
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
