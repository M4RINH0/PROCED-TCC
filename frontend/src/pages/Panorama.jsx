import { useId, useState } from 'react'
import Atualizando from '../components/Atualizando.jsx'
import AvisoAmostra from '../components/AvisoAmostra.jsx'
import EstadoConsulta from '../components/EstadoConsulta.jsx'
import FiltroLocal from '../components/FiltroLocal.jsx'
import GraficoSerie from '../components/GraficoSerie.jsx'
import Icone from '../components/Icone.jsx'
import LeituraAno from '../components/LeituraAno.jsx'
import PainelSimulacao from '../components/PainelSimulacao.jsx'
import { useConsulta } from '../hooks/useConsulta.js'
import { buscarSerie } from '../services/api.js'
import { comSinal, milhoes, umaCasa } from '../utils/formato.js'
import { RECORTES, seriesComDado, valoresDoCenario } from '../utils/series.js'
import { SIMULACAO_PADRAO } from '../utils/simulacao.js'

const LOCAL_PADRAO = { valor: 'Brasil', nome: 'Brasil', regioes: [], aoMudar: () => {} }
const definido = (v) => v !== null && v !== undefined

function frase(ponto, ano, nome) {
  const taxas = ponto?.cenarios.find((c) => c.id === 'taxas')
  if (!taxas || taxas.valor === null) {
    return (
      <>
        Sem dado do método das taxas para <b>{ano}</b> nesta localidade.
      </>
    )
  }
  const { efeito_envelhecimento_kwh: total, efeito_idade_kwh: idade, efeito_arranjos_kwh: arranjos } = ponto
  const totalMes = ponto.efeito_envelhecimento_total_kwh_mes
  return (
    <>
      Em <b>{ano}</b>, pelo método das taxas, os domicílios do recorte ({nome}) consomem <b>{umaCasa(taxas.valor)} kWh/mês por pessoa</b>
      {definido(taxas.variacao_pct) && <>, {comSinal(taxas.variacao_pct)}% em relação a 2026</>}.
      {definido(total) && (
        <>
          {' '}
          O efeito do envelhecimento, a diferença para o contrafactual com a composição de 2026, é de <b>{comSinal(total)} kWh por pessoa</b>
          {definido(idade) && definido(arranjos) && (
            <>
              : {comSinal(idade)} da idade e {comSinal(arranjos)} da mudança de arranjos
            </>
          )}
          {definido(totalMes) && (
            <>
              {' '}
              (<b>{totalMes >= 0 ? '+' : '−'}{milhoes(Math.abs(totalMes))} de kWh/mês</b> no consumo total)
            </>
          )}
          .
        </>
      )}
    </>
  )
}

export default function Panorama({
  ano,
  aoMudarAno,
  versao = 0,
  abrirGaveta = () => {},
  avisar = () => {},
  buscar = buscarSerie,
  local = LOCAL_PADRAO,
  simulacao = SIMULACAO_PADRAO,
}) {
  const idRecorte = useId()
  const [recorte, setRecorte] = useState(RECORTES[0].id)
  const [visiveis, setVisiveis] = useState({ taxas: true, taxas_arranjos_fixos: true, ml_rf: true, ml_gb: true, contrafactual: true })
  const { intensidade, k } = simulacao.aplicados
  const { status, dados, erro, recarregar } = useConsulta(
    (o) => buscar({ recorte, localidade: local.valor, intensidade, k }, o),
    [recorte, local.valor, intensidade, k, versao],
  )
  const anoInteiro = Math.round(ano)
  const opcao = RECORTES.find((r) => r.id === recorte)
  const nomeDosDados = dados ? (local.nomeDe?.(dados.localidade) ?? dados.localidade) : local.nome
  const atualizando = status === 'carregando' && Boolean(dados)

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
          <p className={atualizando ? 'esmaecido' : undefined}>
            {status === 'erro'
              ? 'Dados indisponíveis no momento. Os controles continuam ativos e serão aplicados quando a conexão voltar.'
              : carregando
                ? 'Carregando dados…'
                : frase(ponto, anoInteiro, nomeDosDados)}
          </p>
          <Atualizando ativo={atualizando} destino={local.nome} />
        </div>
        <div className="vh-lado">
          <FiltroLocal local={local} />
          <PainelSimulacao simulacao={simulacao} />
        </div>
      </div>
      <div className="body g-pan">
        <section className={atualizando ? 'pan esmaecido' : 'pan'} aria-labelledby="h-pan">
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
                parametros={`ano ${anoInteiro}, grupo ${opcao.rotulo}, ${local.nome}`}
                aoTentarDeNovo={recarregar}
              />
            </div>
          )}
          {dados && status !== 'erro' && <AvisoAmostra ativo={dados.baixa_confiabilidade} celulas={dados.celulas} />}
          <div className="pf">
            <span>
              {dados?.simulacao && <b>Simulação. </b>}
              Fonte: {dados?.fonte ?? 'POF 2017 a 2018 e Projeções da População (IBGE)'}, {nomeDosDados}.
              {typeof dados?.domicilios_amostra === 'number' &&
                ` Amostra da POF: ${dados.domicilios_amostra.toLocaleString('pt-BR')} domicílios no recorte.`} Linha cheia até o ano
              selecionado; esmaecida depois dele. O gráfico mostra a TBC padronizada: a média por domicílio do consumo per capita.
            </span>
            <button type="button" className="lnk" onClick={() => abrirGaveta('fontes')}>
              Ver fontes
            </button>
          </div>
        </section>
        <aside className={atualizando ? 'pan esmaecido' : 'pan'} aria-labelledby="h-ro">
          <LeituraAno ponto={status === 'erro' ? null : ponto} ano={anoInteiro} series={comDado} visiveis={visiveis} />
          <div className="ctrls">
            <div className="fl">
              <label htmlFor={idRecorte}>
                <Icone nome="target" /> Grupo exibido
              </label>
              <select id={idRecorte} className="recorte-sel" value={recorte} onChange={(e) => setRecorte(e.target.value)}>
                {RECORTES.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.rotulo}
                  </option>
                ))}
              </select>
              <p className="recorte-explica" data-testid="recorte-explica">
                {opcao.explica}
              </p>
            </div>
          </div>
        </aside>
      </div>
    </>
  )
}
