import { useState } from 'react'
import { BarraHorizontal, EstadoConsulta, Segmentado, inteiro, reais, umaCasa, useConsulta } from '../../../shared/index.js'
import { buscarArranjos } from '../api.js'

export const GRUPOS = [
  { id: 'todos', rotulo: 'Todos' },
  { id: 'chefe_60_mais', rotulo: 'Chefe 60+' },
  { id: 'abaixo_60', rotulo: 'Abaixo de 60' },
]

export default function DomiciliosTela({ buscar = buscarArranjos }) {
  const [grupo, setGrupo] = useState('todos')
  const { status, dados, erro, recarregar } = useConsulta((opcoes) => buscar({ grupo }, opcoes), [grupo])
  const linhas = dados?.arranjos ?? []
  const maximo = Math.max(0, ...linhas.map((a) => a.consumo_per_capita_kwh))

  return (
    <>
      <div className="vh">
        <div>
          <h1>Domicílios por arranjo</h1>
          <p>
            Consumo médio por pessoa em cada arranjo domiciliar. O estudo considera <b>mononucleares</b> o unipessoal
            e o casal ou dupla; com chefe de 60 anos ou mais, formam o recorte principal.
          </p>
        </div>
        <Segmentado rotulo="Idade do chefe" opcoes={GRUPOS} valor={grupo} aoMudar={setGrupo} />
      </div>
      <section className="pan" aria-labelledby="h-arranjos">
        <div className="ph">
          <h2 id="h-arranjos">
            Consumo por arranjo <small>kWh/mês por pessoa</small>
          </h2>
        </div>
        <EstadoConsulta
          status={status}
          erro={erro}
          temDados={Boolean(dados)}
          parametros={`idade do chefe ${GRUPOS.find((g) => g.id === grupo).rotulo}`}
          aoTentarDeNovo={recarregar}
        />
        {dados && status !== 'erro' && (
          <div className="twrap">
            <table className="tbl">
              <thead>
                <tr>
                  <th>Arranjo</th>
                  <th>Chefe</th>
                  <th className="n">Domicílios na amostra</th>
                  <th className="n">Por pessoa (kWh/mês)</th>
                  <th aria-hidden="true" />
                  <th className="n">Domicílio (kWh/mês)</th>
                  <th className="n">Gasto médio</th>
                </tr>
              </thead>
              <tbody>
                {linhas.length === 0 && (
                  <tr>
                    <td colSpan={7}>sem dado para este filtro</td>
                  </tr>
                )}
                {linhas.map((a) => {
                  const recorte = a.mononuclear && a.chefe_60_mais
                  return (
                    <tr key={`${a.arranjo}-${a.chefe_60_mais}`} className={recorte ? 'in' : ''}>
                      <td>
                        {a.arranjo}
                        {a.mononuclear && <span className="tag">mononuclear</span>}
                      </td>
                      <td>{a.chefe_60_mais ? '60 anos ou mais' : 'abaixo de 60'}</td>
                      <td className="n">{inteiro(a.domicilios_amostra)}</td>
                      <td className="n">{umaCasa(a.consumo_per_capita_kwh)}</td>
                      <td className="barra-cel">
                        <BarraHorizontal valor={a.consumo_per_capita_kwh} maximo={maximo} destaque={recorte} />
                      </td>
                      <td className="n">{umaCasa(a.consumo_total_kwh)}</td>
                      <td className="n">{reais(a.gasto_rs)}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
        <div className="pf">
          <span>Fonte: {dados?.fonte ?? 'carregando'}. Linhas em destaque: recorte do estudo.</span>
        </div>
      </section>
    </>
  )
}
