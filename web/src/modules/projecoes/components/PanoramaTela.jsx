import { useState } from 'react'
import { EstadoConsulta, Segmentado, useConsulta } from '../../../shared/index.js'
import { buscarSerie, valoresDoCenario } from '../api.js'
import { ANO_FINAL, ANO_FINAL_IBGE, ANO_INICIAL, RECORTES, SERIES } from '../series.js'
import GraficoSerie from './GraficoSerie.jsx'
import LeituraAno from './LeituraAno.jsx'

export default function PanoramaTela({ buscar = buscarSerie }) {
  const [ano, setAno] = useState(ANO_FINAL_IBGE)
  const [recorte, setRecorte] = useState(RECORTES[0].id)
  const { status, dados, erro, recarregar } = useConsulta((opcoes) => buscar({ recorte }, opcoes), [recorte])
  const rotuloRecorte = RECORTES.find((r) => r.id === recorte).rotulo

  const series = dados ? SERIES.map((s) => ({ id: s.id, pontos: valoresDoCenario(dados.pontos, s.id) })) : []
  const modelados = series.filter((s) => s.pontos.some((p) => p.valor !== null)).map((s) => s.id)
  const doAno = dados?.pontos.find((p) => p.ano === ano)

  return (
    <>
      <div className="vh">
        <div>
          <h1>Panorama da projeção</h1>
          <p>
            Consumo residencial per capita dos domicílios mononucleares (unipessoal e casal) de {ANO_INICIAL} a{' '}
            {ANO_FINAL}. O cenário oficial aplica a TEC da POF à estrutura etária projetada pelo IBGE, que vai até{' '}
            {ANO_FINAL_IBGE}.
          </p>
        </div>
      </div>
      <section className="pan" aria-labelledby="h-serie">
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
          </div>
          <Segmentado rotulo="Grupo exibido" opcoes={RECORTES} valor={recorte} aoMudar={setRecorte} />
        </div>
        <div className="ph">
          <h2 id="h-serie">
            Consumo residencial per capita <small>kWh/mês por pessoa</small>
          </h2>
        </div>
        <EstadoConsulta
          status={status}
          erro={erro}
          temDados={Boolean(dados)}
          parametros={`ano ${ano}, grupo ${rotuloRecorte}`}
          aoTentarDeNovo={recarregar}
        />
        {dados && status !== 'erro' && (
          <>
            <div className="plot">
              <GraficoSerie series={series} anoSelecionado={ano} />
            </div>
            <div className="ph">
              <h2>
                Leitura de <span className="ano">{ano}</span>
              </h2>
            </div>
            <LeituraAno cenarios={doAno?.cenarios ?? []} modelados={modelados} />
          </>
        )}
        <div className="pf">
          <span>Fonte: {dados?.fonte ?? 'carregando'}. Premissas em docs/premissas.md.</span>
        </div>
      </section>
    </>
  )
}
