import { useState } from 'react'
import EstadoConsulta from '../components/EstadoConsulta.jsx'
import FiltroLocal from '../components/FiltroLocal.jsx'
import GradeCasas from '../components/GradeCasas.jsx'
import Segmentado from '../components/Segmentado.jsx'
import { useConsulta } from '../hooks/useConsulta.js'
import { buscarComposicao } from '../services/api.js'
import { ANOS_HISTORICO, APARENCIA, FILTROS, noFiltro } from '../utils/categorias.js'
import { umaCasa } from '../utils/formato.js'


function Historico({ categoria, anos, ano, maximo }) {
  const W = 118
  const H = 26
  const bw = 8
  const gp = (W - bw * ANOS_HISTORICO.length) / (ANOS_HISTORICO.length - 1)
  return (
    <svg className="hist hcell" viewBox={`0 0 ${W} ${H}`} aria-hidden="true">
      {ANOS_HISTORICO.map((a, i) => {
        const k = anos.indexOf(a)
        const v = k >= 0 ? categoria.participacao_pct[k] : 0
        const h = Math.max(2, (v / maximo) * (H - 2))
        return (
          <rect
            key={a}
            className={`hb ${APARENCIA[categoria.id].classe}${a <= ano ? ' on' : ''}`}
            data-ano={a}
            x={(i * (bw + gp)).toFixed(1)}
            y={(H - h).toFixed(1)}
            width={bw}
            height={h.toFixed(1)}
            rx="1.5"
          />
        )
      })}
    </svg>
  )
}

const LOCAL_PADRAO = { valor: 'Brasil', nome: 'Brasil', regioes: [], aoMudar: () => {} }

export default function Domicilios({ ano, versao = 0, buscar = buscarComposicao, local = LOCAL_PADRAO }) {
  const [filtro, setFiltro] = useState('todos')
  const [destaque, setDestaque] = useState(null)
  const { status, dados, erro, recarregar } = useConsulta((o) => buscar({ localidade: local.valor }, o), [local.valor, versao])
  const anoInteiro = Math.round(ano)
  const indice = dados ? dados.anos.indexOf(anoInteiro) : -1
  const semDado = dados && indice < 0
  const categorias = dados?.categorias ?? []
  const casas = categorias.map((c) => (indice >= 0 ? c.casas[indice] : 0))
  const recorte = categorias.filter((c) => c.mononuclear && c.chefe_60_mais)
  const maximo = Math.max(1, ...categorias.flatMap((c) => c.participacao_pct))

  let frase = 'Carregando dados…'
  if (status === 'erro') frase = 'Dados indisponíveis no momento. Os controles continuam ativos e serão aplicados quando a conexão voltar.'
  else if (semDado) frase = `Sem dado da composição dos domicílios para ${anoInteiro}.`
  else if (dados) {
    const agora = recorte.reduce((s, c) => s + c.casas[indice], 0)
    const inicio = recorte.reduce((s, c) => s + c.casas[0], 0)
    frase = (
      <>
        Em <b>{anoInteiro}</b>, <b>{agora} de cada 100 domicílios</b> são mononucleares com chefe de 60 anos ou mais ({local.nome}). Em{' '}
        {dados.anos[0]} eram {inicio}.
      </>
    )
  }

  return (
    <>
      <div className="vh">
        <div>
          <h1>Domicílios por arranjo</h1>
          <p>{frase}</p>
        </div>
        <div className="vh-lado">
          <FiltroLocal local={local} />
          <Segmentado rotulo="Filtrar arranjos" opcoes={FILTROS} valor={filtro} aoMudar={setFiltro} />
        </div>
      </div>
      <div className="body g-dom">
        <section className="pan" aria-labelledby="h-iso">
          <div className="ph">
            <h2 id="h-iso">
              Cem domicílios brasileiros <small>cada casa representa 1%</small>
            </h2>
          </div>
          {dados && status !== 'erro' && !semDado ? (
            <GradeCasas categorias={categorias} casas={casas} filtro={filtro} destaque={destaque} />
          ) : (
            <div className="iso">
              {semDado ? (
                <div className="pstate">
                  <h3>Sem dado para {anoInteiro}</h3>
                  <p>A projeção populacional do IBGE não tem este ano.</p>
                </div>
              ) : (
                <EstadoConsulta status={status} erro={erro} temDados={Boolean(dados)} parametros={`ano ${anoInteiro}, ${local.nome}`} aoTentarDeNovo={recarregar} />
              )}
            </div>
          )}
          <div className="isoleg">
            {Object.entries(APARENCIA).map(([id, a]) => (
              <span key={id}>
                <i style={{ background: `var(--${a.cor})` }} />
                {a.nome}
              </span>
            ))}
          </div>
          <div className="pf">
            <span>Fonte: {dados?.fonte ?? 'POF e IBGE'}, {local.nome}. Os arranjos do recorte ocupam as primeiras casas da grade.</span>
          </div>
        </section>
        <section className="pan" aria-labelledby="h-rows">
          <div className="ph">
            <h2 id="h-rows">Consumo por arranjo</h2>
            <small style={{ color: 'var(--muted)', fontSize: 12 }}>Passe o cursor numa linha para destacar as casas</small>
          </div>
          <div className="rows">
            <div className="row hd" aria-hidden="true">
              <span />
              <span>Arranjo</span>
              <span className="v">Domicílios</span>
              <span className="v">kWh/mês</span>
              <span className="hcell">Participação no tempo</span>
            </div>
            {categorias.map((c) => (
              <button
                key={c.id}
                type="button"
                className="row"
                data-testid={`linha-${c.id}`}
                style={{ opacity: noFiltro(c, filtro) ? 1 : 0.42 }}
                onMouseEnter={() => setDestaque(c.id)}
                onMouseLeave={() => setDestaque(null)}
                onFocus={() => setDestaque(c.id)}
                onBlur={() => setDestaque(null)}
              >
                <span className="sw" style={{ background: `var(--${APARENCIA[c.id].cor})` }} />
                <span className="nm">
                  {APARENCIA[c.id].nome}
                  <small>
                    {APARENCIA[c.id].sub}, {c.domicilios_amostra.toLocaleString('pt-BR')} na amostra
                  </small>
                </span>
                <span className="v num">{indice >= 0 ? `${umaCasa(c.participacao_pct[indice])}%` : 'sem dado'}</span>
                <span className="v num">{c.consumo_per_capita_kwh === null ? 'sem dado' : umaCasa(c.consumo_per_capita_kwh)}</span>
                <Historico categoria={c} anos={dados.anos} ano={anoInteiro} maximo={maximo} />
              </button>
            ))}
            {dados && (
              <div className="row tot">
                <span className="sw" style={{ background: 'linear-gradient(90deg,var(--teal) 50%,var(--teal-2) 50%)' }} />
                <span className="nm">
                  Recorte do estudo<small>Unipessoal 60+ e casal de idosos</small>
                </span>
                <span className="v num" data-testid="total-recorte">
                  {indice >= 0 ? `${umaCasa(recorte.reduce((s, c) => s + c.participacao_pct[indice], 0))}%` : 'sem dado'}
                </span>
                <span className="v" />
                <span className="hcell" />
              </div>
            )}
          </div>
          <div className="pf">
            <span>kWh/mês por pessoa, POF 2017 a 2018. Barras acesas: anos até o selecionado na linha do tempo.</span>
          </div>
        </section>
      </div>
    </>
  )
}
