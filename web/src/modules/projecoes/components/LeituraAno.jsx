import { umaCasa } from '../../../shared/index.js'
import { ANO_FINAL_IBGE, SERIES } from '../series.js'

export default function LeituraAno({ cenarios }) {
  const valorDe = (id) => cenarios.find((c) => c.id === id)?.valor ?? null
  return (
    <div className="leitura">
      {SERIES.map((serie) => {
        const valor = valorDe(serie.id)
        return (
          <div className="reg" key={serie.id} data-testid={`reg-${serie.id}`}>
            <span className={`lb c-${serie.id}`}>
              <i className={`t-${serie.id}`} aria-hidden="true" />
              <span style={{ color: 'var(--ink-2)' }}>{serie.rotulo}</span>
            </span>
            {valor === null ? (
              <span className="sem">
                {serie.id === 'ibge' ? `Sem projeção oficial após ${ANO_FINAL_IBGE}` : 'sem dado'}
              </span>
            ) : (
              <span className="v num">
                {umaCasa(valor)}
                <small>kWh/mês por pessoa</small>
              </span>
            )}
          </div>
        )
      })}
    </div>
  )
}
