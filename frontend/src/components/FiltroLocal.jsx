import { useId } from 'react'
import { BRASIL, regiaoDe } from '../utils/localidades.js'

/* Filtro de região e estado, comum a todas as páginas.
   local: { valor, regioes, aoMudar }. O estado só fica disponível depois de escolher a região. */
export default function FiltroLocal({ local }) {
  const id = useId()
  const { valor, regioes, aoMudar } = local
  const regiao = regiaoDe(regioes, valor)
  const estados = regioes.find((r) => r.nome === regiao)?.estados ?? []

  return (
    <div className="filtro-local" role="group" aria-label="Localidade">
      <div className="fl">
        <label htmlFor={`${id}-regiao`}>Região</label>
        <select id={`${id}-regiao`} value={regiao ?? BRASIL} onChange={(e) => aoMudar(e.target.value)}>
          <option value={BRASIL}>Brasil</option>
          {regioes.map((r) => (
            <option key={r.nome} value={r.nome}>
              {r.nome}
            </option>
          ))}
        </select>
      </div>
      <div className="fl">
        <label htmlFor={`${id}-estado`}>Estado</label>
        <select id={`${id}-estado`} value={regiao ? valor : ''} disabled={!regiao} onChange={(e) => aoMudar(e.target.value)}>
          {regiao ? (
            <>
              <option value={regiao}>Todos da região</option>
              {estados.map((e) => (
                <option key={e.sigla} value={e.sigla}>
                  {e.nome}
                </option>
              ))}
            </>
          ) : (
            <option value="">Escolha a região</option>
          )}
        </select>
      </div>
    </div>
  )
}
