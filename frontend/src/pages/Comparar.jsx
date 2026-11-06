import { useId, useState } from 'react'
import Atualizando from '../components/Atualizando.jsx'
import EstadoConsulta from '../components/EstadoConsulta.jsx'
import FiltroLocal from '../components/FiltroLocal.jsx'
import GraficoComparacao from '../components/GraficoComparacao.jsx'
import Icone from '../components/Icone.jsx'
import PainelSimulacao from '../components/PainelSimulacao.jsx'
import Segmentado from '../components/Segmentado.jsx'
import { useConsulta } from '../hooks/useConsulta.js'
import {
  buscarComparacao,
  exportarComparacao,
  buscarSensibilidadeIntensidade,
  buscarSensibilidadeCobertura,
  buscarSinteseRegional,
} from '../services/api.js'
import { salvarBlob } from '../utils/arquivo.js'
import { comSinal, inteiro, umaCasa } from '../utils/formato.js'
import {
  ATALHOS,
  FORMAS,
  GRUPOS,
  GRUPOS_PADRAO,
  INDICADORES_COMPARACAO,
  MAXIMO_GRUPOS,
  MINIMO_GRUPOS,
  estiloDoGrupo,
  formatarPct,
  formatarValor,
  fraseResumo,
  grupoPorId,
  soAgregados,
} from '../utils/comparacao.js'
import { FONTE_COMPARACAO } from '../utils/fontes.js'
import { rotuloDaSerie } from '../utils/series.js'
import { SIMULACAO_PADRAO } from '../utils/simulacao.js'

export const MODOS_COMPARACAO = [
  { id: 'grupos', rotulo: 'Grupos sociodemográficos' },
  { id: 'intensidade', rotulo: 'Sensibilidade Intensidade (I)' },
  { id: 'cobertura', rotulo: 'Sensibilidade Cobertura POF' },
  { id: 'regional', rotulo: 'Síntese Regional' },
]

export const SENSIBILIDADE_INTENSIDADE_PADRAO = [
  { ano: 2050, intensidade: 0.0, tbc_kwh: 74.94, efeito_arranjos_kwh: 0.00, consumo_por_pessoa_kwh: 63.15, consumo_total_bi_kwh: 13.79, part_mono_60_pct: 28.04, div_populacao_pct: 13.72 },
  { ano: 2050, intensidade: 0.5, tbc_kwh: 77.96, efeito_arranjos_kwh: 3.02, consumo_por_pessoa_kwh: 66.09, consumo_total_bi_kwh: 14.43, part_mono_60_pct: 32.53, div_populacao_pct: 5.77 },
  { ano: 2050, intensidade: 0.6, tbc_kwh: 78.52, efeito_arranjos_kwh: 3.59, consumo_por_pessoa_kwh: 66.70, consumo_total_bi_kwh: 14.57, part_mono_60_pct: 33.38, div_populacao_pct: 4.26 },
  { ano: 2050, intensidade: 1.0, tbc_kwh: 80.60, efeito_arranjos_kwh: 5.66, consumo_por_pessoa_kwh: 69.19, consumo_total_bi_kwh: 15.11, part_mono_60_pct: 36.54, div_populacao_pct: -1.39 },
  { ano: 2070, intensidade: 0.0, tbc_kwh: 76.79, efeito_arranjos_kwh: 0.00, consumo_por_pessoa_kwh: 64.58, consumo_total_bi_kwh: 12.87, part_mono_60_pct: 33.26, div_populacao_pct: 18.23 },
  { ano: 2070, intensidade: 0.5, tbc_kwh: 81.85, efeito_arranjos_kwh: 5.06, consumo_por_pessoa_kwh: 70.26, consumo_total_bi_kwh: 14.00, part_mono_60_pct: 42.12, div_populacao_pct: 3.78 },
  { ano: 2070, intensidade: 0.6, tbc_kwh: 82.68, efeito_arranjos_kwh: 5.88, consumo_por_pessoa_kwh: 71.40, consumo_total_bi_kwh: 14.23, part_mono_60_pct: 43.63, div_populacao_pct: 1.33 },
  { ano: 2070, intensidade: 1.0, tbc_kwh: 85.24, efeito_arranjos_kwh: 8.45, consumo_por_pessoa_kwh: 75.62, consumo_total_bi_kwh: 15.07, part_mono_60_pct: 48.59, div_populacao_pct: -6.60 },
]

export const SENSIBILIDADE_COBERTURA_PADRAO = [
  { ano: 2026, fator_peso: 1.0000, cobertura_pct: 92.4, domicilios_mi: 72.39, moradores_mi: 208.54, div_populacao_pct: -2.65, calibracao_p12: 1.0272, tbc_kwh: 71.54, consumo_por_pessoa_kwh: 60.58, consumo_total_bi_kwh: 12.98 },
  { ano: 2026, fator_peso: 1.0819, cobertura_pct: 100.0, domicilios_mi: 78.32, moradores_mi: 225.62, div_populacao_pct: 5.33, calibracao_p12: 0.9494, tbc_kwh: 71.54, consumo_por_pessoa_kwh: 60.58, consumo_total_bi_kwh: 12.98 },
  { ano: 2050, fator_peso: 1.0000, cobertura_pct: 92.4, domicilios_mi: 90.62, moradores_mi: 227.76, div_populacao_pct: 4.26, calibracao_p12: 0.9591, tbc_kwh: 78.52, consumo_por_pessoa_kwh: 66.70, consumo_total_bi_kwh: 14.57 },
  { ano: 2050, fator_peso: 1.0819, cobertura_pct: 100.0, domicilios_mi: 98.04, moradores_mi: 246.42, div_populacao_pct: 12.80, calibracao_p12: 0.8865, tbc_kwh: 78.52, consumo_por_pessoa_kwh: 66.70, consumo_total_bi_kwh: 14.57 },
  { ano: 2070, fator_peso: 1.0000, cobertura_pct: 92.4, domicilios_mi: 88.13, moradores_mi: 201.88, div_populacao_pct: 1.33, calibracao_p12: 0.9869, tbc_kwh: 82.68, consumo_por_pessoa_kwh: 71.40, consumo_total_bi_kwh: 14.23 },
  { ano: 2070, fator_peso: 1.0819, cobertura_pct: 100.0, domicilios_mi: 95.35, moradores_mi: 218.41, div_populacao_pct: 9.63, calibracao_p12: 0.9121, tbc_kwh: 82.68, consumo_por_pessoa_kwh: 71.40, consumo_total_bi_kwh: 14.23 },
]

export const SINTESE_REGIONAL_PADRAO = [
  { localidade: 'Brasil', amostra_pof: 52102, populacao_60_mais_pct_2026: 17.1, populacao_60_mais_pct_2070: 37.8, tbc_2026: 71.54, tbc_2070: 82.68, variacao_tbc_pct: 15.6, part_mono_60_mais_pct_2026: 19.33, part_mono_60_mais_pct_2070: 43.63 },
  { localidade: 'Norte', amostra_pof: 6735, populacao_60_mais_pct_2026: 11.5, populacao_60_mais_pct_2070: 35.9, tbc_2026: 69.02, tbc_2070: 82.78, variacao_tbc_pct: 19.9, part_mono_60_mais_pct_2026: 10.79, part_mono_60_mais_pct_2070: 33.30 },
  { localidade: 'Nordeste', amostra_pof: 17646, populacao_60_mais_pct_2026: 15.8, populacao_60_mais_pct_2070: 39.4, tbc_2026: 52.56, tbc_2070: 62.15, variacao_tbc_pct: 18.2, part_mono_60_mais_pct_2026: 16.41, part_mono_60_mais_pct_2070: 42.29 },
  { localidade: 'Centro-Oeste', amostra_pof: 6175, populacao_60_mais_pct_2026: 14.7, populacao_60_mais_pct_2070: 34.6, tbc_2026: 78.26, tbc_2070: 88.92, variacao_tbc_pct: 13.6, part_mono_60_mais_pct_2026: 16.03, part_mono_60_mais_pct_2070: 38.49 },
  { localidade: 'Sudeste', amostra_pof: 13678, populacao_60_mais_pct_2026: 18.8, populacao_60_mais_pct_2070: 38.4, tbc_2026: 78.04, tbc_2070: 89.40, variacao_tbc_pct: 14.6, part_mono_60_mais_pct_2026: 21.88, part_mono_60_mais_pct_2070: 46.11 },
  { localidade: 'Sul', amostra_pof: 7868, populacao_60_mais_pct_2026: 19.1, populacao_60_mais_pct_2070: 36.8, tbc_2026: 81.65, tbc_2070: 91.60, variacao_tbc_pct: 12.2, part_mono_60_mais_pct_2026: 21.15, part_mono_60_mais_pct_2070: 42.11 },
]

const LOCAL_PADRAO = { valor: 'Brasil', nome: 'Brasil', regioes: [], aoMudar: () => {} }
const CENARIOS = ['taxas', 'taxas_arranjos_fixos', 'contrafactual']
export const EXPLICA_POR_PESSOA =
  'O consumo por pessoa só aparece para agregados: o de uma célula isolada fica nos níveis da POF e não muda com o tempo.'

const duasCasas = (v) => v.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const quatroCasas = (v) => v.toLocaleString('pt-BR', { minimumFractionDigits: 4, maximumFractionDigits: 4 })
const comSinal2 = (v) => (v >= 0 ? '+' : '−') + duasCasas(Math.abs(v))

function Amostra({ id }) {
  const e = estiloDoGrupo(id)
  return (
    <svg className="cmp-amostra" width="22" height="10" aria-hidden="true">
      <line x1="1" x2="21" y1="5" y2="5" stroke={e.cor} strokeWidth={e.espessura} strokeDasharray={e.tracejado} />
    </svg>
  )
}

export default function Comparar({
  abrirGaveta = () => {},
  avisar = () => {},
  buscar = buscarComparacao,
  exportar = exportarComparacao,
  buscarSensInt = buscarSensibilidadeIntensidade,
  buscarSensCob = buscarSensibilidadeCobertura,
  buscarSintReg = buscarSinteseRegional,
  local = LOCAL_PADRAO,
  simulacao = SIMULACAO_PADRAO,
  versao = 0,
}) {
  const id = useId()
  const [modo, setModo] = useState('grupos')
  const [grupos, setGrupos] = useState(GRUPOS_PADRAO)
  const [indicador, setIndicador] = useState('domicilios')
  const [forma, setForma] = useState('indice')
  const [cenario, setCenario] = useState('taxas')
  const [baixando, setBaixando] = useState(false)
  const { intensidade, k } = simulacao.aplicados
  const parametros = { grupos, indicador, forma, cenario, localidade: local.valor, intensidade, k }
  const { status, dados, erro, recarregar } = useConsulta(
    (o) => buscar(parametros, o),
    [grupos.join(','), indicador, forma, cenario, local.valor, intensidade, k, versao],
  )
  const sensInt = useConsulta((o) => buscarSensInt(o), [versao])
  const sensCob = useConsulta((o) => buscarSensCob(o), [versao])
  const sintReg = useConsulta((o) => buscarSintReg(o), [versao])
  const dadosIntensidade = sensInt.dados?.linhas ?? SENSIBILIDADE_INTENSIDADE_PADRAO
  const dadosCobertura = sensCob.dados?.linhas ?? SENSIBILIDADE_COBERTURA_PADRAO
  const dadosRegional = sintReg.dados?.linhas ?? SINTESE_REGIONAL_PADRAO

  const atualizando = status === 'carregando' && Boolean(dados)
  const porPessoaDisponivel = soAgregados(grupos)
  const resumo = dados ? fraseResumo(dados.tabela, rotuloDaSerie(dados.cenario)) : null
  const nomeDosDados = dados ? (local.nomeDe?.(dados.localidade) ?? dados.localidade) : local.nome
  const semValor = dados ? dados.grupos.filter((g) => g.motivo_sem_valor) : []

  const alternarGrupo = (gid) => {
    if (grupos.includes(gid)) {
      if (grupos.length <= MINIMO_GRUPOS) return avisar(`Mantenha ao menos ${MINIMO_GRUPOS} grupos`)
      return setGrupos(grupos.filter((g) => g !== gid))
    }
    if (grupos.length >= MAXIMO_GRUPOS) return avisar(`Escolha no máximo ${MAXIMO_GRUPOS} grupos`)
    const novos = GRUPOS.map((g) => g.id).filter((g) => g === gid || grupos.includes(g))
    if (indicador === 'consumo_por_pessoa' && !soAgregados(novos)) {
      setIndicador('domicilios')
      avisar('Consumo por pessoa só vale para agregados: o indicador voltou para o número de domicílios')
    }
    return setGrupos(novos)
  }

  const usarAtalho = (atalho) => {
    setGrupos(atalho.grupos)
    if (indicador === 'consumo_por_pessoa' && !soAgregados(atalho.grupos)) setIndicador('domicilios')
  }

  const baixar = async (formato) => {
    setBaixando(true)
    try {
      const { blob, nomeArquivo } = await exportar({ ...parametros, formato })
      salvarBlob(blob, nomeArquivo || `proced_comparacao.${formato}`)
      avisar(`Comparação exportada em ${formato.toUpperCase()}`)
    } catch {
      avisar('Não foi possível exportar a comparação')
    } finally {
      setBaixando(false)
    }
  }

  let frase = 'Carregando dados…'
  if (status === 'erro') frase = 'Dados indisponíveis no momento. Os controles continuam ativos e serão aplicados quando a conexão voltar.'
  else if (dados) frase = resumo ? resumo.texto : 'Sem valor para comparar o crescimento destes grupos nesta localidade.'

  return (
    <>
      <div className="vh vh-compacto">
        <div>
          <h1>Comparar grupos</h1>
          <p className={atualizando ? 'esmaecido' : undefined} data-testid="frase-comparacao">
            {modo === 'grupos'
              ? frase
              : modo === 'intensidade'
                ? 'Análise de sensibilidade do parâmetro de intensidade (I) da transição dos arranjos.'
                : modo === 'cobertura'
                  ? 'Análise de sensibilidade da cobertura amostral da POF 2017 a 2018 e teorema de invariância.'
                  : 'Síntese comparativa regional entre o Brasil e as 5 macrorregiões.'}
          </p>
          <Atualizando ativo={atualizando} destino={local.nome} />
        </div>
      </div>

      <div style={{ marginBottom: 16 }}>
        <Segmentado rotulo="Visão de comparação" opcoes={MODOS_COMPARACAO} valor={modo} aoMudar={setModo} />
      </div>

      {modo === 'grupos' && (
        <>
          <div className="barra-filtros barra-cmp" role="group" aria-label="Filtros da comparação">
            <FiltroLocal local={local} />
            <div className="fl fl-indicador">
              <label htmlFor={`${id}-indicador`}>Indicador</label>
              <select id={`${id}-indicador`} className="recorte-sel" value={indicador} onChange={(e) => setIndicador(e.target.value)}>
                {INDICADORES_COMPARACAO.map((i) => (
                  <option key={i.id} value={i.id} disabled={i.soAgregados && !porPessoaDisponivel}>
                    {i.rotulo}
                  </option>
                ))}
              </select>
            </div>
            <Segmentado rotulo="Forma" opcoes={FORMAS} valor={forma} aoMudar={setForma} />
            <div className="fl fl-cenario">
              <label htmlFor={`${id}-cenario`}>Cenário</label>
              <select id={`${id}-cenario`} className="recorte-sel" value={cenario} onChange={(e) => setCenario(e.target.value)}>
                {CENARIOS.map((c) => (
                  <option key={c} value={c}>
                    {rotuloDaSerie(c)}
                  </option>
                ))}
              </select>
            </div>
            <PainelSimulacao simulacao={simulacao} />
          </div>

          <section className="pan cmp-grupos" aria-labelledby={`${id}-g`}>
            <div className="ph">
              <h2 id={`${id}-g`}>
                Grupos <small>de {MINIMO_GRUPOS} a {MAXIMO_GRUPOS}, {grupos.length} escolhidos</small>
              </h2>
              <div className="cmp-atalhos" role="group" aria-label="Atalhos">
                {ATALHOS.map((a) => (
                  <button key={a.id} type="button" className="lnk" onClick={() => usarAtalho(a)}>
                    {a.rotulo}
                  </button>
                ))}
              </div>
            </div>
            <div className="cmp-chips">
              {[
                ['Células', GRUPOS.filter((g) => g.arranjo)],
                ['Agregados', GRUPOS.filter((g) => !g.arranjo)],
              ].map(([titulo, lista]) => (
                <div key={titulo} className="cmp-linha" role="group" aria-label={titulo}>
                  <span className="flab">{titulo}</span>
                  {lista.map((g) => (
                    <button key={g.id} type="button" className="lt" aria-pressed={grupos.includes(g.id)} onClick={() => alternarGrupo(g.id)}>
                      <Amostra id={g.id} />
                      {g.rotulo}
                    </button>
                  ))}
                </div>
              ))}
            </div>
            {!porPessoaDisponivel && <p className="recorte-explica" data-testid="explica-por-pessoa">{EXPLICA_POR_PESSOA}</p>}
          </section>

          <div className="body g-cmp">
            <section className={atualizando ? 'pan esmaecido' : 'pan'} aria-labelledby={`${id}-graf`}>
              <div className="ph">
                <h2 id={`${id}-graf`}>
                  {INDICADORES_COMPARACAO.find((i) => i.id === indicador).rotulo.replace(' (só agregados)', '')}{' '}
                  <small>{forma === 'indice' ? 'índice, 2026 = 100' : (dados?.unidade ?? '')}</small>
                </h2>
              </div>
              {dados && status !== 'erro' ? (
                <GraficoComparacao grupos={dados.grupos} forma={dados.forma} unidade={dados.unidade} />
              ) : (
                <div className="plot plot-cmp">
                  <EstadoConsulta
                    status={status}
                    erro={erro}
                    temDados={Boolean(dados)}
                    parametros={`${grupos.map((g) => grupoPorId(g).rotulo).join(', ')}, ${local.nome}`}
                    aoTentarDeNovo={recarregar}
                  />
                </div>
              )}
              <div className="pf">
                <span>
                  {dados?.simulacao && <b>Simulação. </b>}
                  Fonte: {dados?.fonte ?? FONTE_COMPARACAO}, {nomeDosDados}. Cenário {rotuloDaSerie(cenario).toLowerCase()}.
                </span>
                <button type="button" className="lnk" onClick={() => abrirGaveta('fontes')}>
                  Ver fontes
                </button>
              </div>
            </section>

            <section className={atualizando ? 'pan esmaecido' : 'pan'} aria-labelledby={`${id}-tab`}>
              <div className="ph">
                <h2 id={`${id}-tab`}>
                  Crescimento de 2026 a 2070 <small>{dados?.unidade ?? ''}</small>
                </h2>
              </div>
              <div className="twrap">
                <table className="tbl" data-testid="tabela-comparacao">
                  <thead>
                    <tr>
                      <th>Grupo</th>
                      <th className="n">2026</th>
                      <th className="n">2050</th>
                      <th className="n">2070</th>
                      <th className="n">Variação</th>
                      <th className="n">Variação %</th>
                      <th className="n">Ordem</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(dados && status !== 'erro' ? dados.tabela : []).map((l) => (
                      <tr key={l.id}>
                        <td>
                          <span className="cmp-nome">
                            <Amostra id={l.id} />
                            {l.rotulo}
                          </span>
                        </td>
                        <td className="n">{formatarValor(l.valor_2026, indicador)}</td>
                        <td className="n">{formatarValor(l.valor_2050, indicador)}</td>
                        <td className="n">{formatarValor(l.valor_2070, indicador)}</td>
                        <td className="n">{formatarValor(l.variacao_absoluta, indicador, { sinal: true })}</td>
                        <td className="n">{formatarPct(l.variacao_pct)}</td>
                        <td className="n">{l.ordem === null ? 'sem dado' : `${l.ordem}º`}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {semValor.length > 0 && (
                <ul className="cmp-motivos" data-testid="motivos-sem-valor">
                  {semValor.map((g) => (
                    <li key={g.id}>
                      <b>{g.rotulo}:</b> {g.motivo_sem_valor}
                    </li>
                  ))}
                </ul>
              )}
              {dados?.grupos.some((g) => g.baixa_confiabilidade && !g.motivo_sem_valor) && (
                <div className="aviso-amostra" role="note" data-testid="aviso-amostra">
                  <Icone nome="alert" />
                  <span>
                    Baixa confiabilidade: há célula com menos de 30 domicílios na amostra da POF em{' '}
                    {dados.grupos
                      .filter((g) => g.baixa_confiabilidade && !g.motivo_sem_valor)
                      .map((g) => g.rotulo.toLowerCase())
                      .join(', ')}
                    .
                  </span>
                </div>
              )}
              <div className="pf">
                <span>Variação e ordem pelo valor de 2026 e de 2070; 1º é o grupo que mais cresce em %.</span>
                <span className="cmp-baixar">
                  <button type="button" className="btn" disabled={baixando || status === 'erro'} onClick={() => baixar('xlsx')}>
                    <Icone nome="down" />
                    XLSX
                  </button>
                  <button type="button" className="btn" disabled={baixando || status === 'erro'} onClick={() => baixar('csv')}>
                    <Icone nome="down" />
                    CSV
                  </button>
                </span>
              </div>
            </section>
          </div>
        </>
      )}

      {modo === 'intensidade' && (
        <section className="pan" aria-labelledby={`${id}-sens-int`}>
          <div className="ph">
            <h2 id={`${id}-sens-int`}>
              Sensibilidade da Intensidade (I)
            </h2>
          </div>
          <p className="recorte-explica" style={{ margin: '0 20px 16px' }}>
            Variação da intensidade de transição dos arranjos domiciliares para 2050 e 2070. O parâmetro <i>I = 0,60</i> representa o cenário de referência. <i>I = 0,00</i> mantém os arranjos congelados no nível de 2026 e <i>I = 1,00</i> simula a convergência total de arranjos.
          </p>
          <div className="twrap">
            <table className="tbl" data-testid="tabela-sensibilidade-intensidade">
              <thead>
                <tr>
                  <th className="n">Ano</th>
                  <th className="n">Intensidade (I)</th>
                  <th className="n">TBC (kWh/mês)</th>
                  <th className="n">Efeito arranjos (kWh)</th>
                  <th className="n">Consumo/pessoa (kWh)</th>
                  <th className="n">Consumo total (bi kWh)</th>
                  <th className="n">Part. Mono 60+ (%)</th>
                  <th className="n">Div. populacional (%)</th>
                </tr>
              </thead>
              <tbody>
                {dadosIntensidade.map((l, idx) => (
                  <tr key={`${l.ano}-${l.intensidade}-${idx}`}>
                    <td className="n"><b>{l.ano}</b></td>
                    <td className="n">{duasCasas(l.intensidade)}</td>
                    <td className="n">{duasCasas(l.tbc_kwh)}</td>
                    <td className="n">{comSinal2(l.efeito_arranjos_kwh)}</td>
                    <td className="n">{duasCasas(l.consumo_por_pessoa_kwh)}</td>
                    <td className="n">{duasCasas(l.consumo_total_bi_kwh)}</td>
                    <td className="n">{duasCasas(l.part_mono_60_pct)}%</td>
                    <td className="n">{comSinal2(l.div_populacao_pct)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="pf">
            <span>Fonte: {sensInt.dados?.fonte ?? FONTE_COMPARACAO}, Brasil.</span>
            <button type="button" className="lnk" onClick={() => abrirGaveta('fontes')}>
              Ver fontes
            </button>
          </div>
        </section>
      )}

      {modo === 'cobertura' && (
        <section className="pan" aria-labelledby={`${id}-sens-cob`}>
          <div className="ph">
            <h2 id={`${id}-sens-cob`}>
              Sensibilidade da Cobertura Amostral da POF
            </h2>
          </div>
          <p className="recorte-explica" style={{ margin: '0 20px 16px' }}>
            Demonstração do <b>Teorema da Invariância</b> (P12): a expansão dos pesos amostrais (fator 1,0819 para cobrir 100% da população) eleva o número de domicílios e moradores, mas é perfeitamente neutralizada pelo ajuste do fator de calibração P12 (de 1,0272 para 0,9494), mantendo a Taxa Básica de Consumo (TBC) e o consumo total rigorosamente invariantes.
          </p>
          <div className="twrap">
            <table className="tbl" data-testid="tabela-sensibilidade-cobertura">
              <thead>
                <tr>
                  <th className="n">Ano</th>
                  <th className="n">Fator peso</th>
                  <th className="n">Cobertura (%)</th>
                  <th className="n">Domicílios (mi)</th>
                  <th className="n">Moradores (mi)</th>
                  <th className="n">Div. pop. (%)</th>
                  <th className="n">Calibração (P12)</th>
                  <th className="n">TBC (kWh/mês)</th>
                  <th className="n">Consumo/pessoa (kWh)</th>
                  <th className="n">Consumo total (bi kWh)</th>
                </tr>
              </thead>
              <tbody>
                {dadosCobertura.map((l, idx) => (
                  <tr key={`${l.ano}-${l.cobertura_pct}-${idx}`}>
                    <td className="n"><b>{l.ano}</b></td>
                    <td className="n">{quatroCasas(l.fator_peso)}</td>
                    <td className="n">{umaCasa(l.cobertura_pct)}%</td>
                    <td className="n">{duasCasas(l.domicilios_mi)}</td>
                    <td className="n">{duasCasas(l.moradores_mi)}</td>
                    <td className="n">{comSinal2(l.div_populacao_pct)}%</td>
                    <td className="n">{quatroCasas(l.calibracao_p12)}</td>
                    <td className="n"><b>{duasCasas(l.tbc_kwh)}</b></td>
                    <td className="n">{duasCasas(l.consumo_por_pessoa_kwh)}</td>
                    <td className="n"><b>{duasCasas(l.consumo_total_bi_kwh)}</b></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="pf">
            <span>Fonte: {sensCob.dados?.fonte ?? FONTE_COMPARACAO}, Brasil.</span>
            <button type="button" className="lnk" onClick={() => abrirGaveta('fontes')}>
              Ver fontes
            </button>
          </div>
        </section>
      )}

      {modo === 'regional' && (
        <section className="pan" aria-labelledby={`${id}-sint-reg`}>
          <div className="ph">
            <h2 id={`${id}-sint-reg`}>
              Síntese Comparativa Regional
            </h2>
          </div>
          <p className="recorte-explica" style={{ margin: '0 20px 16px' }}>
            Comparação dos indicadores-chave de transição demográfica e consumo elétrico residencial entre o Brasil e as 5 macrorregiões geográficas de 2026 a 2070.
          </p>
          <div className="twrap">
            <table className="tbl" data-testid="tabela-sintese-regional">
              <thead>
                <tr>
                  <th>Localidade</th>
                  <th className="n">Amostra POF</th>
                  <th className="n">Pop. 60+ 2026 (%)</th>
                  <th className="n">Pop. 60+ 2070 (%)</th>
                  <th className="n">TBC 2026 (kWh)</th>
                  <th className="n">TBC 2070 (kWh)</th>
                  <th className="n">Variação TBC %</th>
                  <th className="n">Part. Mono 60+ 2026 (%)</th>
                  <th className="n">Part. Mono 60+ 2070 (%)</th>
                </tr>
              </thead>
              <tbody>
                {dadosRegional.map((l) => (
                  <tr key={l.localidade}>
                    <td><b>{l.localidade}</b></td>
                    <td className="n">{inteiro(l.amostra_pof)}</td>
                    <td className="n">{umaCasa(l.populacao_60_mais_pct_2026)}%</td>
                    <td className="n">{umaCasa(l.populacao_60_mais_pct_2070)}%</td>
                    <td className="n">{duasCasas(l.tbc_2026)}</td>
                    <td className="n">{duasCasas(l.tbc_2070)}</td>
                    <td className="n">{comSinal(l.variacao_tbc_pct)}%</td>
                    <td className="n">{duasCasas(l.part_mono_60_mais_pct_2026)}%</td>
                    <td className="n">{duasCasas(l.part_mono_60_mais_pct_2070)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="pf">
            <span>Fonte: {sintReg.dados?.fonte ?? FONTE_COMPARACAO}.</span>
            <button type="button" className="lnk" onClick={() => abrirGaveta('fontes')}>
              Ver fontes
            </button>
          </div>
        </section>
      )}
    </>
  )
}
