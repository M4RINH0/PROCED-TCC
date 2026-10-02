import { useState } from 'react'
import FiltroLocal from '../components/FiltroLocal.jsx'
import Icone from '../components/Icone.jsx'
import Odometro from '../components/Odometro.jsx'
import { useConsulta } from '../hooks/useConsulta.js'
import { useTamanho } from '../hooks/useTamanho.js'
import { buscarSimulacao } from '../services/api.js'
import { lerTaxa, umaCasa } from '../utils/formato.js'

export const ANOS = [2030, 2035, 2040, 2045, 2050, 2055, 2060, 2065, 2070]
export const FAIXAS = [
  { id: 'ate_29', rotulo: 'até 29' },
  { id: '30_39', rotulo: '30 a 39' },
  { id: '40_49', rotulo: '40 a 49' },
  { id: '50_59', rotulo: '50 a 59' },
  { id: '60_69', rotulo: '60 a 69' },
  { id: '70_79', rotulo: '70 a 79' },
  { id: '80_mais', rotulo: '80+' },
]
export const ARRANJOS = [
  { id: 'unipessoal', rotulo: 'Unipessoal' },
  { id: 'casal_ou_dupla', rotulo: 'Casal ou dupla' },
  { id: 'multipessoal', rotulo: 'Multipessoal (3 ou mais)' },
]
export const BASES = [
  { id: 'ibge', rotulo: 'Oficial IBGE' },
  { id: 'mod', rotulo: 'Modelo próprio' },
  { id: 'alt', rotulo: 'Alternativo (ML)' },
]
const PADRAO = { ano: '2070', faixa: '70_79', arranjo: 'unipessoal', base: 'ibge', taxa: '1,7' }
const rotulo = (lista, id) => lista.find((x) => x.id === id).rotulo

function HistoricoFaixas({ porFaixa, faixa }) {
  const [ref, { largura: W, altura: H }] = useTamanho({ largura: 600, altura: 170 })
  const m = { t: 18, b: 20 }
  const n = porFaixa.length
  const gp = Math.max(6, W * 0.018)
  const bw = Math.min(46, (W - gp * (n - 1)) / n)
  const ox = (W - (bw * n + gp * (n - 1))) / 2
  const mx = Math.max(1, ...porFaixa.map((f) => f.consumo_per_capita_kwh ?? 0)) * 1.05
  return (
    <div className="bill-hist" ref={ref}>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Consumo por pessoa em cada faixa do chefe para o arranjo escolhido">
        <line className="bl" x1="0" x2={W} y1={H - m.b} y2={H - m.b} />
        {porFaixa.map((f, i) => {
          const v = f.consumo_per_capita_kwh ?? 0
          const h = Math.max(2, (v / mx) * (H - m.t - m.b))
          const x = ox + i * (bw + gp)
          const atual = f.faixa === rotulo(FAIXAS, faixa)
          return (
            <g key={f.faixa}>
              <rect className={atual ? 'hb2 last' : 'hb2'} x={x.toFixed(1)} y={(H - m.b - h).toFixed(1)} width={bw.toFixed(1)} height={h.toFixed(1)} rx="3" />
              <text className="hlab" x={(x + bw / 2).toFixed(1)} y={H - 5} textAnchor="middle">
                {f.faixa}
              </text>
              {f.consumo_per_capita_kwh !== null && (
                <text className="hval" x={(x + bw / 2).toFixed(1)} y={(H - m.b - h - 5).toFixed(1)} textAnchor="middle">
                  {umaCasa(v)}
                </text>
              )}
            </g>
          )
        })}
      </svg>
    </div>
  )
}

const LOCAL_PADRAO = { valor: 'Brasil', nome: 'Brasil', regioes: [], aoMudar: () => {} }

export default function Simulador({ versao = 0, avisar = () => {}, buscar = buscarSimulacao, local = LOCAL_PADRAO }) {
  const [form, setForm] = useState(PADRAO)
  const taxa = lerTaxa(form.taxa)
  const valido = taxa !== null
  const params = { ano: Number(form.ano), faixa: form.faixa, arranjo: form.arranjo, base: form.base, taxa, localidade: local.valor }
  const { status, dados, erro, recarregar } = useConsulta(
    (o) => (valido ? buscar(params, o) : Promise.resolve(null)),
    [form.ano, form.faixa, form.arranjo, form.base, taxa, local.valor, versao],
  )
  const mudar = (campo) => (e) => setForm((f) => ({ ...f, [campo]: e.target.value }))

  let corpo
  if (!valido) {
    corpo = (
      <div className="bill-state">
        <h3>
          <Icone nome="alert" />
          Consulta não realizada
        </h3>
        <p>Corrija a taxa de envelhecimento para calcular o cenário.</p>
      </div>
    )
  } else if (status === 'erro') {
    corpo = (
      <div className="bill-state" role="alert">
        <h3>
          <Icone nome="alert" />
          Não foi possível calcular o cenário
        </h3>
        <p>{erro?.message}. Os parâmetros foram mantidos; tente novamente.</p>
        <button type="button" className="btn" onClick={recarregar} style={{ marginTop: 8 }}>
          <Icone nome="refresh" />
          Tentar novamente
        </button>
      </div>
    )
  } else if (!dados) {
    corpo = (
      <div className="bill-load" aria-busy="true" aria-label="Calculando">
        <div className="skel" style={{ width: '40%' }} />
        <div className="skel" style={{ width: '70%' }} />
        <div className="skel sk-big" />
      </div>
    )
  } else if (dados.valor === null) {
    corpo = (
      <div className="bill-state">
        <h3>
          <Icone nome="info" />
          Sem dados para esta combinação
        </h3>
        <p>{dados.motivo_sem_valor} Troque o ano ou a base de projeção.</p>
      </div>
    )
  } else {
    corpo = (
      <>
        <div className="bill-main">
          <div>
            <Odometro valor={dados.valor} unidade="kWh/mês por pessoa" />
          </div>
          <p className="bill-read">
            Em <b>{dados.ano}</b>, um domicílio <b>{rotulo(ARRANJOS, form.arranjo).toLowerCase()}</b> com chefe na faixa de{' '}
            <b>{dados.faixa}</b> consome <b>{umaCasa(dados.valor)} kWh por mês por pessoa</b> no cenário oficial, média de{' '}
            {dados.domicilios_amostra.toLocaleString('pt-BR')} domicílios da POF. Nesse cenário o valor de cada tipo de domicílio
            fica nos níveis da POF; o ano define se há projeção oficial.
          </p>
        </div>
        <HistoricoFaixas porFaixa={dados.por_faixa} faixa={form.faixa} />
        <div className="bill-f">
          <span className="chip">
            <i />
            <span>Calculado a partir da POF; salvar cenários (RF09) ainda não foi implementado</span>
          </span>
          <span>Fonte: {dados.fonte}</span>
          <button type="button" className="btn" onClick={() => avisar('Exportação ainda não implementada (RF08)')}>
            <Icone nome="down" />
            Exportar resultado
          </button>
        </div>
      </>
    )
  }

  return (
    <>
      <div className="vh">
        <div>
          <h1>Simulador de cenário</h1>
          <p>Combine os parâmetros para obter o consumo projetado de um tipo de domicílio num ano específico.</p>
        </div>
        <div className="vh-lado">
          <FiltroLocal local={local} />
        </div>
      </div>
      <div className="body g-sim">
        <section className="pan" aria-labelledby="h-form">
          <form
            className="form"
            noValidate
            onSubmit={(e) => {
              e.preventDefault()
              if (valido) recarregar()
            }}
          >
            <h2 id="h-form" className="sr">
              Parâmetros
            </h2>
            <div className="fgrid">
              <div className="fl">
                <label htmlFor="fAno">Ano de referência</label>
                <select id="fAno" value={form.ano} onChange={mudar('ano')}>
                  {ANOS.map((a) => (
                    <option key={a}>{a}</option>
                  ))}
                </select>
              </div>
              <div className="fl">
                <label htmlFor="fFai">Faixa do chefe</label>
                <select id="fFai" value={form.faixa} onChange={mudar('faixa')}>
                  {FAIXAS.map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.rotulo}
                    </option>
                  ))}
                </select>
              </div>
              <div className="fl full">
                <label htmlFor="fArr">Arranjo domiciliar</label>
                <select id="fArr" value={form.arranjo} onChange={mudar('arranjo')}>
                  {ARRANJOS.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.rotulo}
                    </option>
                  ))}
                </select>
              </div>
              <div className="fl">
                <label htmlFor="fTaxa">Taxa anual (%)</label>
                <input
                  type="text"
                  id="fTaxa"
                  value={form.taxa}
                  onChange={mudar('taxa')}
                  inputMode="decimal"
                  autoComplete="off"
                  aria-describedby="fTaxaMsg"
                  aria-invalid={!valido}
                  className={valido ? '' : 'err'}
                />
                {valido ? (
                  <div id="fTaxaMsg" className="help">
                    De 0 a 10; usada pelo cenário do modelo
                  </div>
                ) : (
                  <div id="fTaxaMsg" className="errm">
                    <Icone nome="alert" />
                    Informe um número entre 0 e 10, como 1,7.
                  </div>
                )}
              </div>
              <div className="fl full">
                <label htmlFor="fBase">Base de projeção</label>
                <select id="fBase" value={form.base} onChange={mudar('base')}>
                  {BASES.map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.rotulo}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <button type="submit" className="btn pri wide" disabled={!valido}>
              Consultar cenário
            </button>
            <button type="button" className="lnk" style={{ alignSelf: 'flex-start' }} onClick={() => setForm(PADRAO)}>
              Restaurar parâmetros
            </button>
            <p className="help" style={{ margin: 0 }}>
              A consulta atualiza a cada mudança. O botão repete a consulta sob demanda.
            </p>
          </form>
        </section>
        <section className="pan" aria-labelledby="h-bill">
          <div className="bill">
            <div className="bill-h">
              <b id="h-bill">Demonstrativo de consumo projetado</b>
              <span>POF 2017 a 2018 e IBGE, {local.nome}</span>
            </div>
            <dl className="bill-kv">
              {[
                ['Unidade', rotulo(ARRANJOS, form.arranjo)],
                ['Faixa do chefe', rotulo(FAIXAS, form.faixa)],
                ['Ano de referência', form.ano],
                ['Base', rotulo(BASES, form.base)],
              ].map(([k, v]) => (
                <div key={k}>
                  <dt>{k}</dt>
                  <dd>{v}</dd>
                </div>
              ))}
            </dl>
            <div style={{ display: 'flex', flexDirection: 'column', flex: '1 1 auto', minHeight: 0 }}>{corpo}</div>
          </div>
        </section>
      </div>
    </>
  )
}
