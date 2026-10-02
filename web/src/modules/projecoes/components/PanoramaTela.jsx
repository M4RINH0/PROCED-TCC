import { useState } from 'react'
import { buscarProjecao } from '../api.js'
import { useProjecao } from '../hooks/useProjecao.js'
import { ANO_FINAL, ANO_FINAL_IBGE, ANO_INICIAL, RECORTES } from '../series.js'
import LeituraAno from './LeituraAno.jsx'

export default function PanoramaTela({ buscar = buscarProjecao }) {
  const [ano, setAno] = useState(ANO_FINAL)
  const [recorte, setRecorte] = useState(RECORTES[0].id)
  const { status, dados, erro, recarregar } = useProjecao({ ano, recorte }, buscar)
  const rotuloRecorte = RECORTES.find((r) => r.id === recorte).rotulo

  return (
    <>
      <div className="vh">
        <div>
          <h1>Panorama da projeção</h1>
          <p>
            Consumo residencial per capita projetado de {ANO_INICIAL} a {ANO_FINAL}, comparado à projeção oficial do
            IBGE, que termina em {ANO_FINAL_IBGE}.
          </p>
        </div>
      </div>
      <section className="pan" aria-labelledby="h-leitura">
        <div className="ctrls">
          <div className="fl">
            <label htmlFor="ano">
              Ano <span className="ano">{ano}</span>
            </label>
            <input
              id="ano"
              type="range"
              min={ANO_INICIAL}
              max={ANO_FINAL}
              step={1}
              value={ano}
              onChange={(e) => setAno(Number(e.target.value))}
              aria-valuetext={String(ano)}
            />
            {ano > ANO_FINAL_IBGE && (
              <div className="pf" style={{ padding: '4px 0 0' }}>
                Sem projeção oficial após {ANO_FINAL_IBGE}
              </div>
            )}
          </div>
          <div className="fl">
            <span className="flab" id="recorte-rotulo">
              Grupo exibido
            </span>
            <div className="seg" role="group" aria-labelledby="recorte-rotulo">
              {RECORTES.map((r) => (
                <button key={r.id} type="button" aria-pressed={recorte === r.id} onClick={() => setRecorte(r.id)}>
                  {r.rotulo}
                </button>
              ))}
            </div>
          </div>
        </div>
        <div className="ph">
          <h2 id="h-leitura">
            Leitura do ano <small>kWh/mês por pessoa</small>
          </h2>
        </div>
        {status === 'carregando' && !dados && (
          <div aria-busy="true" aria-label="Carregando dados">
            <div className="skel" style={{ width: '40%' }} />
            <div className="skel" style={{ width: '70%' }} />
          </div>
        )}
        {status === 'erro' && (
          <div className="pstate erro" role="alert">
            <h3>Não foi possível carregar a projeção</h3>
            <p>
              {erro?.message}. Os parâmetros foram mantidos: ano <b>{ano}</b>, grupo <b>{rotuloRecorte}</b>.
            </p>
            <button type="button" className="btn" onClick={recarregar}>
              Tentar novamente
            </button>
          </div>
        )}
        {dados && status !== 'erro' && <LeituraAno cenarios={dados.cenarios} />}
        <div className="pf">
          <span>
            Fonte: <span className="pend">a definir</span>
            {dados?.dados_ilustrativos && '. Valores ilustrativos, não decorrem de apuração.'}
          </span>
        </div>
      </section>
    </>
  )
}
