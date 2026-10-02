import { useState } from 'react'
import { BarraHorizontal, EstadoConsulta, inteiro, umaCasa, useConsulta } from '../../../shared/index.js'
import { buscarConsumoChefe, buscarPiramide } from '../api.js'
import Piramide from './Piramide.jsx'

export const ANO_INICIAL = 2026
export const ANO_FINAL = 2070 // fim da projeção populacional do IBGE

export const ARRANJOS = [
  { id: 'mononucleares', rotulo: 'Mononucleares (unipessoal e casal)' },
  { id: 'unipessoal', rotulo: 'Unipessoal' },
  { id: 'casal_ou_dupla', rotulo: 'Casal ou dupla' },
  { id: 'multipessoal', rotulo: 'Multipessoal (3 ou mais)' },
  { id: 'todos', rotulo: 'Todos os arranjos' },
]

const FAIXAS_60 = new Set(['60 a 69', '70 a 79', '80+'])

export default function EstruturaEtariaTela({ buscarPir = buscarPiramide, buscarConsumo = buscarConsumoChefe }) {
  const [ano, setAno] = useState(ANO_INICIAL)
  const [arranjo, setArranjo] = useState('mononucleares')
  const piramide = useConsulta((o) => buscarPir({ ano }, o), [ano])
  const consumo = useConsulta((o) => buscarConsumo({ arranjo }, o), [arranjo])
  const faixas = consumo.dados?.faixas ?? []
  const maximo = Math.max(0, ...faixas.map((f) => f.consumo_per_capita_kwh ?? 0))

  return (
    <>
      <div className="vh">
        <div>
          <h1>Estrutura etária</h1>
          <p>
            {piramide.dados ? (
              <>
                Em <b>{piramide.dados.ano}</b>, a população de <b>60 anos ou mais</b> é{' '}
                <b>{umaCasa(piramide.dados.participacao_60_mais_pct)}%</b> do total.
              </>
            ) : (
              'Pirâmide etária projetada pelo IBGE e consumo por faixa etária do chefe do domicílio.'
            )}
          </p>
        </div>
      </div>
      <div className="grade-2">
        <section className="pan" aria-labelledby="h-pir">
          <div className="ctrls">
            <div className="fl">
              <label htmlFor="ano-pir">
                Ano <span className="ano">{ano}</span>
              </label>
              <input
                id="ano-pir"
                type="range"
                min={ANO_INICIAL}
                max={ANO_FINAL}
                step={1}
                value={ano}
                onChange={(e) => setAno(Number(e.target.value))}
                aria-valuetext={String(ano)}
              />
            </div>
          </div>
          <div className="ph">
            <h2 id="h-pir">
              Pirâmide etária <small>% da população</small>
            </h2>
          </div>
          <EstadoConsulta
            status={piramide.status}
            erro={piramide.erro}
            temDados={Boolean(piramide.dados)}
            parametros={`ano ${ano}`}
            aoTentarDeNovo={piramide.recarregar}
          />
          {piramide.dados && piramide.status !== 'erro' && (
            <div className="plot">
              <Piramide faixas={piramide.dados.faixas} />
            </div>
          )}
          <div className="pf">
            <span>Fonte: {piramide.dados?.fonte ?? 'carregando'}. Projeção disponível até {ANO_FINAL}.</span>
          </div>
        </section>

        <section className="pan" aria-labelledby="h-chefe">
          <div className="ctrls">
            <div className="fl">
              <label htmlFor="arranjo">Arranjo domiciliar</label>
              <select id="arranjo" className="sel" value={arranjo} onChange={(e) => setArranjo(e.target.value)}>
                {ARRANJOS.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.rotulo}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="ph">
            <h2 id="h-chefe">
              Consumo por faixa etária do chefe <small>kWh/mês por pessoa</small>
            </h2>
          </div>
          <EstadoConsulta
            status={consumo.status}
            erro={consumo.erro}
            temDados={Boolean(consumo.dados)}
            parametros={`arranjo ${ARRANJOS.find((a) => a.id === arranjo).rotulo}`}
            aoTentarDeNovo={consumo.recarregar}
          />
          {consumo.dados && consumo.status !== 'erro' && (
            <div className="twrap">
              <table className="tbl">
                <thead>
                  <tr>
                    <th>Faixa do chefe</th>
                    <th className="n">Domicílios na amostra</th>
                    <th className="n">Por pessoa</th>
                    <th aria-hidden="true" />
                    <th>No estudo</th>
                  </tr>
                </thead>
                <tbody>
                  {[...faixas].reverse().map((f) => {
                    const idoso = FAIXAS_60.has(f.faixa)
                    return (
                      <tr key={f.faixa} className={idoso ? 'in' : ''}>
                        <td>{f.faixa}</td>
                        <td className="n">{inteiro(f.domicilios_amostra)}</td>
                        <td className="n">{f.consumo_per_capita_kwh === null ? 'sem dado' : umaCasa(f.consumo_per_capita_kwh)}</td>
                        <td className="barra-cel">
                          <BarraHorizontal valor={f.consumo_per_capita_kwh ?? 0} maximo={maximo} destaque={idoso} />
                        </td>
                        <td>{idoso ? 'Recorte' : 'Comparação'}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
          <div className="pf">
            <span>Fonte: {consumo.dados?.fonte ?? 'carregando'}.</span>
          </div>
        </section>
      </div>
    </>
  )
}
