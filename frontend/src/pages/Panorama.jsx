import { useState } from 'react'
import AvisoAmostra from '../components/AvisoAmostra.jsx'
import EstadoConsulta from '../components/EstadoConsulta.jsx'
import FiltroLocal from '../components/FiltroLocal.jsx'
import GraficoSerie from '../components/GraficoSerie.jsx'
import Icone from '../components/Icone.jsx'
import LeituraAno from '../components/LeituraAno.jsx'
import { useConsulta } from '../hooks/useConsulta.js'
import { buscarSerie } from '../services/api.js'
import { comSinal, milhoes, umaCasa } from '../utils/formato.js'
import { RECORTES, seriesComDado, valoresDoCenario } from '../utils/series.js'


const LOCAL_PADRAO = { valor: 'Brasil', nome: 'Brasil', regioes: [], aoMudar: () => {} }

function frase(ponto, ano, nome) {
  const taxas = ponto?.cenarios.find((c) => c.id === 'taxas')
  if (!taxas || taxas.valor === null) {
    return (
      <>
        Sem dado do método das taxas para <b>{ano}</b> nesta localidade.
      </>
    )
  }
  const efeito = ponto.efeito_envelhecimento_kwh
  const efeitoTotal = ponto.efeito_envelhecimento_total_kwh_mes
  return (
    <>
      Em <b>{ano}</b>, pelo método das taxas, os domicílios do recorte ({nome}) consomem <b>{umaCasa(taxas.valor)} kWh/mês por pessoa</b>
      {taxas.variacao_pct !== null && taxas.variacao_pct !== undefined && <>, {comSinal(taxas.variacao_pct)}% em relação a 2026</>}.
      {efeito !== null && efeito !== undefined && (
        <>
          {' '}
          O efeito do envelhecimento, a diferença para o contrafactual com a composição de 2026, é de <b>{comSinal(efeito)} kWh por pessoa</b>
          {efeitoTotal !== null && efeitoTotal !== undefined && (
            <>
              {' '}
              e de <b>{efeitoTotal >= 0 ? '+' : '−'}{milhoes(Math.abs(efeitoTotal))} de kWh/mês</b> no consumo total
            </>
          )}
          .
        </>
      )}
    </>
  )
}

export default function Panorama({ ano, aoMudarAno, versao = 0, abrirGaveta = () => {}, avisar = () => {}, buscar = buscarSerie, local = LOCAL_PADRAO }) {
  const [recorte, setRecorte] = useState(RECORTES[0].id)
  const [visiveis, setVisiveis] = useState({ taxas: true, ml_rf: true, ml_gb: true, contrafactual: true })
  const { status, dados, erro, recarregar } = useConsulta((o) => buscar({ recorte, localidade: local.valor }, o), [recorte, local.valor, versao])
  const anoInteiro = Math.round(ano)
  const rotuloRecorte = RECORTES.find((r) => r.id === recorte).rotulo

  const comDado = dados ? seriesComDado(dados.pontos) : []
  const series = comDado.map((s) => ({ id: s.id, pontos: valoresDoCenario(dados.pontos, s.id) }))
  const ponto = dados?.pontos.find((p) => p.ano === anoInteiro)
  const carregando = status === 'carregando' && !dados

  const alternar = (id) => {
    if (visiveis[id] && comDado.filter((s) => visiveis[s.id]).length === 1) {
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
                : frase(ponto, anoInteiro, local.nome)}
          </p>
        </div>
        <div className="vh-lado">
          <FiltroLocal local={local} />
          <span className="rec">
            <Icone nome="target" />
            Recorte: domicílio mononuclear (unipessoal e casal), chefe {recorte === 'chefe_60_mais' ? 'com 60 anos ou mais' : 'abaixo de 60 anos'}
          </span>
        </div>
      </div>
      <div className="body g-pan">
        <section className="pan" aria-labelledby="h-pan">
          <div className="ph">
            <h2 id="h-pan">
              Consumo residencial per capita <small>kWh/mês</small>
            </h2>
            <div className="leg" role="group" aria-label="Séries exibidas">
              {comDado.map((s) => (
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
              {comDado.length > 1 && (
                <span className="lt" style={{ cursor: 'default', color: 'var(--ink-2)' }} aria-hidden="true">
                  <i className="band" />
                  Diferença entre cenários
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
                parametros={`ano ${anoInteiro}, grupo ${rotuloRecorte}, ${local.nome}`}
                aoTentarDeNovo={recarregar}
              />
            </div>
          )}
          {dados && status !== 'erro' && <AvisoAmostra ativo={dados.baixa_confiabilidade} celulas={dados.celulas} />}
          <div className="pf">
            <span>
              Fonte: {dados?.fonte ?? 'POF 2017 a 2018 e Projeções da População (IBGE)'}, {local.nome}.
              {typeof dados?.domicilios_amostra === 'number' &&
                ` Amostra da POF: ${dados.domicilios_amostra.toLocaleString('pt-BR')} domicílios no recorte.`} Linha cheia até o ano
              selecionado; esmaecida depois dele. O gráfico mostra a TBC padronizada: a média por domicílio do consumo per capita.
            </span>
            <button type="button" className="lnk" onClick={() => abrirGaveta('fontes')}>
              Ver fontes
            </button>
          </div>
        </section>
        <aside className="pan" aria-labelledby="h-ro">
          <LeituraAno ponto={status === 'erro' ? null : ponto} ano={anoInteiro} series={comDado} visiveis={visiveis} />
          <div className="ctrls">
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
