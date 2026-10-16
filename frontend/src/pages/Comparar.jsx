import { useId, useState } from 'react'
import Atualizando from '../components/Atualizando.jsx'
import EstadoConsulta from '../components/EstadoConsulta.jsx'
import FiltroLocal from '../components/FiltroLocal.jsx'
import GraficoComparacao from '../components/GraficoComparacao.jsx'
import Icone from '../components/Icone.jsx'
import PainelSimulacao from '../components/PainelSimulacao.jsx'
import Segmentado from '../components/Segmentado.jsx'
import { useConsulta } from '../hooks/useConsulta.js'
import { buscarComparacao, exportarComparacao } from '../services/api.js'
import { salvarBlob } from '../utils/arquivo.js'
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

const LOCAL_PADRAO = { valor: 'Brasil', nome: 'Brasil', regioes: [], aoMudar: () => {} }
const CENARIOS = ['taxas', 'taxas_arranjos_fixos', 'contrafactual']
export const EXPLICA_POR_PESSOA =
  'O consumo por pessoa só aparece para agregados: o de uma célula isolada fica nos níveis da POF e não muda com o tempo.'

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
  local = LOCAL_PADRAO,
  simulacao = SIMULACAO_PADRAO,
  versao = 0,
}) {
  const id = useId()
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
            {frase}
          </p>
          <Atualizando ativo={atualizando} destino={local.nome} />
        </div>
      </div>
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
  )
}
