import { useState } from 'react'
import { EstadoConsulta, Icone, comSinal, umaCasa, useConsulta } from '../../../shared/index.js'
import { buscarSerie, valoresDoCenario } from '../api.js'
import { ANO_FINAL_IBGE, RECORTES, SERIES } from '../series.js'
import GraficoSerie from './GraficoSerie.jsx'
import LeituraAno from './LeituraAno.jsx'

function frase(ponto, ano) {
  const ibge = ponto?.cenarios.find((c) => c.id === 'ibge')
  if (!ibge || ibge.valor === null) {
    return (
      <>
        Em <b>{ano}</b> não há projeção oficial: a série do IBGE termina em {ANO_FINAL_IBGE}. O cenário do modelo ainda
        não foi formulado.
      </>
    )
  }
  return (
    <>
      Em <b>{ano}</b>, a projeção oficial é de <b>{umaCasa(ibge.valor)} kWh/mês por pessoa</b> nos domicílios do recorte
      {ibge.variacao_pct !== null && ibge.variacao_pct !== undefined && <>, {comSinal(ibge.variacao_pct)}% em relação a 2026</>}.
      O cenário do modelo ainda não foi formulado.
    </>
  )
}

export default function PanoramaTela({ ano, aoMudarAno, versao = 0, abrirGaveta = () => {}, avisar = () => {}, buscar = buscarSerie }) {
  const [recorte, setRecorte] = useState(RECORTES[0].id)
  const [visiveis, setVisiveis] = useState({ mod: true, ibge: true, alt: true })
  const { status, dados, erro, recarregar } = useConsulta((o) => buscar({ recorte }, o), [recorte, versao])
  const anoInteiro = Math.round(ano)
  const rotuloRecorte = RECORTES.find((r) => r.id === recorte).rotulo

  const series = dados ? SERIES.map((s) => ({ id: s.id, pontos: valoresDoCenario(dados.pontos, s.id) })) : []
  const modelados = series.filter((s) => s.pontos.some((p) => p.valor !== null)).map((s) => s.id)
  const ponto = dados?.pontos.find((p) => p.ano === anoInteiro)
  const carregando = status === 'carregando' && !dados

  const alternar = (id) => {
    if (visiveis[id] && Object.values(visiveis).filter(Boolean).length === 1) {
      avisar('Mantenha ao menos uma série visível')
      return
    }
    setVisiveis((v) => ({ ...v, [id]: !v[id] }))
  }

  return (
    <>
      <div className="vh">
        <div>
          <h1>Panorama da projeção</h1>
          <p>
            {status === 'erro'
              ? 'Dados indisponíveis no momento. Os controles continuam ativos e serão aplicados quando a conexão voltar.'
              : carregando
                ? 'Carregando dados…'
                : frase(ponto, anoInteiro)}
          </p>
        </div>
        <span className="rec">
          <Icone nome="target" />
          Recorte: domicílio mononuclear (unipessoal e casal), chefe {recorte === 'chefe_60_mais' ? 'com 60 anos ou mais' : 'abaixo de 60 anos'}
        </span>
      </div>
      <div className="body g-pan">
        <section className="pan" aria-labelledby="h-pan">
          <div className="ph">
            <h2 id="h-pan">
              Consumo residencial per capita <small>kWh/mês</small>
            </h2>
            <div className="leg" role="group" aria-label="Séries exibidas">
              {SERIES.map((s) => (
                <button
                  key={s.id}
                  type="button"
                  className="lt"
                  aria-pressed={visiveis[s.id]}
                  style={{ color: `var(--${s.cor})` }}
                  onClick={() => alternar(s.id)}
                >
                  <i style={{ borderTopStyle: s.traco }} />
                  <span style={{ color: 'var(--ink-2)' }}>{s.curto}</span>
                </button>
              ))}
              {modelados.length > 1 && (
                <span className="lt" style={{ cursor: 'default', color: 'var(--ink-2)' }} aria-hidden="true">
                  <i className="band" />
                  Intervalo entre cenários
                </span>
              )}
            </div>
          </div>
          {dados && status !== 'erro' ? (
            <GraficoSerie series={series} visiveis={visiveis} ano={ano} aoMudarAno={aoMudarAno} />
          ) : (
            <div className="plot">
              <EstadoConsulta
                status={status}
                erro={erro}
                temDados={Boolean(dados)}
                parametros={`ano ${anoInteiro}, grupo ${rotuloRecorte}`}
                aoTentarDeNovo={recarregar}
              />
            </div>
          )}
          <div className="pf">
            <span>Fonte: {dados?.fonte ?? 'POF e IBGE'}. Linha cheia até o ano selecionado; esmaecida depois dele.</span>
            <button type="button" className="lnk" onClick={() => abrirGaveta('fontes')}>
              Ver fontes
            </button>
          </div>
        </section>
        <aside className="pan" aria-labelledby="h-ro">
          <LeituraAno ponto={status === 'erro' ? null : ponto} ano={anoInteiro} modelados={modelados} visiveis={visiveis} />
          <div className="ctrls">
            <div className="fl">
              <div className="rangeh">
                <label htmlFor="taxa">Taxa de envelhecimento anual</label>
                <output htmlFor="taxa">sem dado</output>
              </div>
              <input className="tx" type="range" id="taxa" min="0.5" max="4" step="0.1" defaultValue="1.7" disabled aria-describedby="taxaHelp" />
              <div className="help" id="taxaHelp">
                Ajusta o cenário do modelo (RF02), que ainda não foi formulado. A projeção oficial não depende dela.
              </div>
            </div>
            <div className="fl">
              <span className="flab" id="recLab">
                Grupo exibido
              </span>
              <div className="seg" role="group" aria-labelledby="recLab">
                {RECORTES.map((r) => (
                  <button key={r.id} type="button" aria-pressed={recorte === r.id} onClick={() => setRecorte(r.id)}>
                    {r.rotulo}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </aside>
      </div>
    </>
  )
}
