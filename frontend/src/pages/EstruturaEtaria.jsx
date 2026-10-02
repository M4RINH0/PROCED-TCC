import { useState } from 'react'
import BarrasFaixa from '../components/BarrasFaixa.jsx'
import EstadoConsulta from '../components/EstadoConsulta.jsx'
import Icone from '../components/Icone.jsx'
import Piramide from '../components/Piramide.jsx'
import { useConsulta } from '../hooks/useConsulta.js'
import { buscarConsumoChefe, buscarPiramides } from '../services/api.js'
import { inteiro, umaCasa } from '../utils/formato.js'


export const ARRANJOS = [
  { id: 'mononucleares', rotulo: 'Mononucleares' },
  { id: 'unipessoal', rotulo: 'Unipessoal' },
  { id: 'casal_ou_dupla', rotulo: 'Casal ou dupla' },
  { id: 'multipessoal', rotulo: 'Multipessoal' },
  { id: 'todos', rotulo: 'Todos' },
]

const FAIXAS_60 = new Set(['60 a 69', '70 a 79', '80+'])

export default function EstruturaEtaria({ ano, versao = 0, buscarPir = buscarPiramides, buscarConsumo = buscarConsumoChefe }) {
  const [arranjo, setArranjo] = useState('mononucleares')
  const pir = useConsulta((o) => buscarPir(o), [versao])
  const consumo = useConsulta((o) => buscarConsumo({ arranjo }, o), [arranjo, versao])
  const anoInteiro = Math.round(ano)
  const piramides = pir.dados?.piramides ?? []
  const doAno = piramides.find((p) => p.ano === anoInteiro)
  const inicial = piramides[0]
  const faixas = consumo.dados?.faixas ?? []
  const rotuloArranjo = ARRANJOS.find((a) => a.id === arranjo).rotulo

  let frase = 'Carregando dados…'
  if (pir.status === 'erro') frase = 'Dados indisponíveis no momento. Os controles continuam ativos e serão aplicados quando a conexão voltar.'
  else if (pir.dados && !doAno) frase = `Sem dado da pirâmide etária para ${anoInteiro}.`
  else if (doAno && inicial) {
    frase = (
      <>
        A população de <b>60 anos ou mais</b> passa de <b>{umaCasa(inicial.participacao_60_mais_pct)}%</b> em {inicial.ano} para{' '}
        <b>{umaCasa(doAno.participacao_60_mais_pct)}%</b> em {anoInteiro}. Onde o contorno de {inicial.ano} fica dentro da barra, a faixa cresceu.
      </>
    )
  }

  return (
    <>
      <div className="vh">
        <div>
          <h1>Estrutura etária</h1>
          <p>{frase}</p>
        </div>
        <span className="rec">
          <Icone nome="target" />
          Recorte: chefe com 60 anos ou mais
        </span>
      </div>
      <div className="body g-eta">
        <section className="pan" aria-labelledby="h-pyr">
          <div className="ph">
            <h2 id="h-pyr">
              Pirâmide etária <small>% da população</small>
            </h2>
            <div className="leg">
              <span className="lt" style={{ cursor: 'default' }}>
                <i className="band" style={{ background: 'var(--teal)' }} />
                60 anos ou mais
              </span>
              <span className="lt" style={{ cursor: 'default' }}>
                <i className="band" style={{ background: 'var(--c5)' }} />
                Abaixo de 60
              </span>
              <span className="lt" style={{ cursor: 'default', color: 'var(--ink-2)' }}>
                <i style={{ borderTop: '1.4px dashed currentColor' }} />
                Contorno de 2026
              </span>
            </div>
          </div>
          {doAno && pir.status !== 'erro' ? (
            <Piramide faixas={doAno.faixas} contorno={inicial.faixas} />
          ) : (
            <div className="plot">
              {pir.dados && pir.status !== 'erro' ? (
                <div className="pstate">
                  <h3>Sem dado para {anoInteiro}</h3>
                  <p>A projeção populacional do IBGE não tem este ano.</p>
                </div>
              ) : (
                <EstadoConsulta status={pir.status} erro={pir.erro} temDados={Boolean(pir.dados)} parametros={`ano ${anoInteiro}`} aoTentarDeNovo={pir.recarregar} />
              )}
            </div>
          )}
          <div className="pf">
            <span>Fonte: {pir.dados?.fonte ?? 'IBGE'}. Arraste a linha do tempo para ver a pirâmide mudar de forma.</span>
          </div>
        </section>
        <section className="pan split-v" aria-labelledby="h-ch">
          <div className="ph">
            <h2 id="h-ch">
              Consumo por faixa etária do chefe <small>kWh/mês por pessoa</small>
            </h2>
            <div className="seg" role="group" aria-label="Arranjo domiciliar">
              {ARRANJOS.map((a) => (
                <button key={a.id} type="button" aria-pressed={arranjo === a.id} onClick={() => setArranjo(a.id)}>
                  {a.rotulo}
                </button>
              ))}
            </div>
          </div>
          {consumo.dados && consumo.status !== 'erro' ? (
            <>
              <BarrasFaixa faixas={faixas} />
              <div className="twrap">
                <table className="tbl">
                  <thead>
                    <tr>
                      <th>Faixa do chefe</th>
                      <th className="n">Domicílios na amostra</th>
                      <th className="n">kWh/mês por pessoa</th>
                      <th>No estudo</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[...faixas].reverse().map((f) => (
                      <tr key={f.faixa} className={FAIXAS_60.has(f.faixa) ? 'in' : ''}>
                        <td>{f.faixa}</td>
                        <td className="n">{inteiro(f.domicilios_amostra)}</td>
                        <td className="n">{f.consumo_per_capita_kwh === null ? 'sem dado' : umaCasa(f.consumo_per_capita_kwh)}</td>
                        <td>{FAIXAS_60.has(f.faixa) ? 'Recorte' : 'Comparação'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <div className="plot">
              <EstadoConsulta
                status={consumo.status}
                erro={consumo.erro}
                temDados={Boolean(consumo.dados)}
                parametros={`arranjo ${rotuloArranjo}`}
                aoTentarDeNovo={consumo.recarregar}
                mudo={pir.status === 'erro'}
              />
            </div>
          )}
          <div className="pf">
            <span>Fonte: {consumo.dados?.fonte ?? 'POF'}. A POF retrata 2017 a 2018; o valor de cada faixa não muda com o ano.</span>
          </div>
        </section>
      </div>
    </>
  )
}
