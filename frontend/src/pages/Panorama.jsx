import { useId, useState } from 'react'
import Atualizando from '../components/Atualizando.jsx'
import AvisoAmostra from '../components/AvisoAmostra.jsx'
import EstadoConsulta from '../components/EstadoConsulta.jsx'
import FiltroLocal from '../components/FiltroLocal.jsx'
import GraficoSerie from '../components/GraficoSerie.jsx'
import LeituraAno from '../components/LeituraAno.jsx'
import PainelSimulacao from '../components/PainelSimulacao.jsx'
import { useConsulta } from '../hooks/useConsulta.js'
import { buscarSerie } from '../services/api.js'
import { comSinal, umaCasa } from '../utils/formato.js'
import {
  INDICADORES,
  efeitoDoIndicador,
  indicadorDisponivel,
  indicadorPadrao,
  porId,
  serieDoIndicador,
  valorDoIndicador,
} from '../utils/indicadores.js'
import { RECORTES, SERIES, seriesComDado } from '../utils/series.js'
import { SIMULACAO_PADRAO } from '../utils/simulacao.js'

const LOCAL_PADRAO = { valor: 'Brasil', nome: 'Brasil', regioes: [], aoMudar: () => {} }
const definido = (v) => v !== null && v !== undefined
const rotulo = (id) => SERIES.find((s) => s.id === id).rotulo.toLowerCase()

function comUnidade(v, indicador) {
  return `${umaCasa(v)}${indicador.sufixo ? indicador.sufixo : ` ${indicador.unidade}`}`
}

function frase(ponto, ano, nome, indicador) {
  const taxas = ponto?.cenarios.find((c) => c.id === 'taxas')
  const valor = valorDoIndicador(taxas, indicador)
  if (valor === null) {
    return (
      <>
        Sem dado do cenário {rotulo('taxas')} para <b>{ano}</b> nesta localidade.
      </>
    )
  }
  const [total, idade, arranjos] = ['envelhecimento', 'idade', 'arranjos'].map((n) => efeitoDoIndicador(ponto, n, indicador))
  return (
    <>
      Em <b>{ano}</b>, no cenário {rotulo('taxas')}, {indicador.titulo.toLowerCase()} dos domicílios do recorte ({nome}) é de{' '}
      <b>{comUnidade(valor, indicador)}</b>
      {indicador.id === 'tbc' && definido(taxas.variacao_pct) && <>, {comSinal(taxas.variacao_pct)}% em relação a 2026</>}.
      {definido(total) && (
        <>
          {' '}
          Em relação ao cenário {rotulo('contrafactual')}, o envelhecimento soma <b>{comSinal(total)} {indicador.unidadeEfeito}</b>
          {definido(idade) && definido(arranjos) && (
            <>
              : {comSinal(idade)} da idade e {comSinal(arranjos)} da mudança de arranjos
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
  const id = useId()
  const [recorte, setRecorte] = useState(RECORTES[0].id)
  const [idIndicador, setIdIndicador] = useState(indicadorPadrao(RECORTES[0].id))
  const [visiveis, setVisiveis] = useState({ taxas: true, taxas_arranjos_fixos: true, ml_rf: true, ml_gb: true, contrafactual: true })
  const { intensidade, k } = simulacao.aplicados
  const { status, dados, erro, recarregar } = useConsulta(
    (o) => buscar({ recorte, localidade: local.valor, intensidade, k }, o),
    [recorte, local.valor, intensidade, k, versao],
  )
  const anoInteiro = Math.round(ano)
  const opcao = RECORTES.find((r) => r.id === recorte)
  const indicador = porId(idIndicador)
  const nomeDosDados = dados ? (local.nomeDe?.(dados.localidade) ?? dados.localidade) : local.nome
  const atualizando = status === 'carregando' && Boolean(dados)

  const comDado = dados ? seriesComDado(dados.pontos) : []
  const series = comDado.map((s) => ({ id: s.id, pontos: serieDoIndicador(dados.pontos, s.id, indicador) }))
  const ponto = dados?.pontos.find((p) => p.ano === anoInteiro)
  const carregando = status === 'carregando' && !dados

  const mudarRecorte = (novo) => {
    setRecorte(novo)
    setIdIndicador(indicadorPadrao(novo))  // cada recorte abre no indicador que mostra o seu efeito
  }

  const alternar = (serie) => {
    if (visiveis[serie] && comDado.filter((s) => visiveis[s.id]).length === 1) {
      avisar('Mantenha ao menos uma série visível')
      return
    }
    setVisiveis((v) => ({ ...v, [serie]: !v[serie] }))
  }

  return (
    <>
      <div className="vh vh-compacto">
        <div>
          <h1>Panorama da projeção</h1>
          <p className={atualizando ? 'esmaecido' : undefined}>
            {status === 'erro'
              ? 'Dados indisponíveis no momento. Os controles continuam ativos e serão aplicados quando a conexão voltar.'
              : carregando
                ? 'Carregando dados…'
                : frase(ponto, anoInteiro, nomeDosDados, indicador)}
          </p>
          <Atualizando ativo={atualizando} destino={local.nome} />
        </div>
      </div>
      <div className="barra-filtros" role="group" aria-label="Filtros do Panorama">
        <FiltroLocal local={local} />
        <div className="fl">
          <label htmlFor={`${id}-recorte`}>Grupo exibido</label>
          <select id={`${id}-recorte`} className="recorte-sel" value={recorte} onChange={(e) => mudarRecorte(e.target.value)}>
            {RECORTES.map((r) => (
              <option key={r.id} value={r.id}>
                {r.rotulo}
              </option>
            ))}
          </select>
        </div>
        <div className="fl fl-indicador">
          <label htmlFor={`${id}-indicador`}>Indicador do gráfico</label>
          <select id={`${id}-indicador`} className="recorte-sel" value={idIndicador} onChange={(e) => setIdIndicador(e.target.value)}>
            {INDICADORES.map((i) => (
              <option key={i.id} value={i.id} disabled={!indicadorDisponivel(i.id, recorte)}>
                {i.rotulo}
                {indicadorDisponivel(i.id, recorte) ? '' : ' (sempre 100% neste recorte)'}
              </option>
            ))}
          </select>
        </div>
        <PainelSimulacao simulacao={simulacao} />
      </div>
      <div className="body g-pan">
        <section className={atualizando ? 'pan esmaecido' : 'pan'} aria-labelledby="h-pan">
          <div className="ph">
            <h2 id="h-pan">
              {indicador.titulo} <small>{indicador.unidade}</small>
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
          <p className="recorte-explica" data-testid="recorte-explica">
            {opcao.explica}
          </p>
          {dados && status !== 'erro' ? (
            <GraficoSerie
              series={series}
              visiveis={visiveis}
              ano={ano}
              aoMudarAno={aoMudarAno}
              eixo={indicador.eixo}
              sufixo={indicador.sufixo}
              descricao={indicador.titulo}
            />
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
              selecionado; esmaecida depois dele.
            </span>
            <button type="button" className="lnk" onClick={() => abrirGaveta('fontes')}>
              Ver fontes
            </button>
          </div>
        </section>
        <aside className={atualizando ? 'pan esmaecido' : 'pan'} aria-labelledby="h-ro">
          <LeituraAno ponto={status === 'erro' ? null : ponto} ano={anoInteiro} series={comDado} visiveis={visiveis} indicador={indicador} />
        </aside>
      </div>
    </>
  )
}
