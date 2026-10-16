import { useEffect, useRef, useState } from 'react'
import { useConsulta } from '../hooks/useConsulta.js'
import { buscarFontes, buscarProjecao, exportarDados } from '../services/api.js'
import { umaCasa } from '../utils/formato.js'
import { PADRAO_SIMULACAO } from '../utils/simulacao.js'
import Icone from './Icone.jsx'
import { ANO_FINAL, ANO_INICIAL } from './LinhaDoTempo.jsx'

function Cabecalho({ icone, titulo, aoFechar }) {
  return (
    <div className="dr-h">
      <h2 id="drT">
        <Icone nome={icone} />
        {titulo}
      </h2>
      <button type="button" className="ib" aria-label="Fechar" onClick={aoFechar}>
        <Icone nome="x" />
      </button>
    </div>
  )
}

function Fontes() {
  const { status, dados } = useConsulta((o) => buscarFontes(o), [])
  return (
    <div className="dr-b">
      {status === 'erro' && <p className="pend">Não foi possível carregar as fontes.</p>}
      <dl>
        {(dados?.fontes ?? []).map((f) => (
          <div className="kv" key={f.id}>
            <dt>{f.nome}</dt>
            <dd>
              {f.periodo}
              <br />
              <small style={{ color: 'var(--muted)' }}>{f.uso}</small>
            </dd>
          </div>
        ))}
      </dl>
      {dados && (
        <>
          <p className="lbl">Critério de exclusão</p>
          <p data-testid="criterio">
            {dados.criterio_exclusao} A base cobre <b>{umaCasa(dados.cobertura_pct)}%</b> dos domicílios estimados pela POF.
          </p>
          <p className="lbl">Premissas principais</p>
          <dl>
            {dados.premissas.map((p) => (
              <div className="kv" key={p.id}>
                <dt>{p.id}</dt>
                <dd>{p.texto}</dd>
              </div>
            ))}
          </dl>
          <a className="lnk" href={dados.premissas_url} target="_blank" rel="noreferrer">
            Todas as premissas em docs/premissas.md
          </a>
        </>
      )}
      <p className="lbl">Como ler o Panorama</p>
      <dl data-testid="como-ler">
        <div className="kv">
          <dt>Envelhecimento e arranjos</dt>
          <dd>A população envelhece como na projeção da população do IBGE, e a divisão entre quem mora só, em dupla ou com mais pessoas segue a tendência das POFs.</dd>
        </div>
        <div className="kv">
          <dt>Só o envelhecimento</dt>
          <dd>A população envelhece, mas a divisão entre os arranjos fica como em 2026.</dd>
        </div>
        <div className="kv">
          <dt>Sem mudanças desde 2026</dt>
          <dd>O número de domicílios cresce como na projeção, mas a composição por idade do chefe e arranjo fica a de 2026.</dd>
        </div>
        <div className="kv">
          <dt>Efeitos</dt>
          <dd>
            Efeito da idade = só o envelhecimento menos sem mudanças desde 2026. Efeito dos arranjos = envelhecimento e
            arranjos menos só o envelhecimento. Os dois somam o efeito do envelhecimento, calculado em cada indicador.
          </dd>
        </div>
      </dl>
      <div className="note-box">
        O IBGE projeta só a população; o consumo de energia é calculado pelo PROCED. A API lê o banco no Supabase só pelo
        back-end.
      </div>
    </div>
  )
}

function Api({ ano, localidade, simulacao, avisar }) {
  const params = { ano: Math.round(ano), recorte: 'todos_domicilios', localidade, ...simulacao }
  const { status, dados } = useConsulta((o) => buscarProjecao(params, o), [params.ano, localidade, simulacao.intensidade, simulacao.k])
  const texto = dados ? JSON.stringify(dados, null, 2) : status === 'erro' ? 'Não foi possível consultar a API.' : 'Consultando…'
  return (
    <>
      <div className="dr-b">
        <div className="warn">
          <Icone nome="info" />
          <span>Resposta real da API para o ano da linha do tempo (RF11). A documentação completa fica em /docs, gerada pelo código (RNF09).</span>
        </div>
        <div className="method">
          <em>GET</em>
          <span>
            /projecoes?ano={params.ano}&amp;recorte={params.recorte}&amp;localidade={params.localidade}&amp;intensidade={params.intensidade}&amp;k={params.k}
          </span>
        </div>
        <pre className="code">{texto}</pre>
      </div>
      <div className="dr-f">
        <button
          type="button"
          className="btn wide"
          onClick={() => navigator.clipboard?.writeText(texto).then(() => avisar('Resposta copiada'), () => avisar('Não foi possível copiar'))}
        >
          <Icone nome="copy" />
          Copiar resposta
        </button>
      </div>
    </>
  )
}

function salvarBlob(blob, nomeArquivo) {
  const url = URL.createObjectURL?.(blob)
  if (!url) return
  const link = document.createElement('a')
  link.href = url
  link.download = nomeArquivo
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL?.(url)
}

function Exportar({ ano, localidade, simulacao, aoFechar, avisar, exportar = exportarDados }) {
  const [formato, setFormato] = useState('xlsx')  // recomendado para planilha
  const [escopo, setEscopo] = useState('ano')
  const [baixando, setBaixando] = useState(false)
  const anoInteiro = Math.round(ano)

  const confirmar = async () => {
    setBaixando(true)
    try {
      const padrao = `proced_${localidade.replace(/\s+/g, '_')}_${escopo === 'ano' ? anoInteiro : `${ANO_INICIAL}_${ANO_FINAL}`}.${formato}`
      const { blob, nomeArquivo } = await exportar({
        formato,
        escopo,
        ano: anoInteiro,
        localidade,
        ...simulacao,
      })
      salvarBlob(blob, nomeArquivo || padrao)
      aoFechar()
      avisar(`Dados exportados em ${formato.toUpperCase()}`)
    } catch {
      avisar('Não foi possível exportar os dados')
    } finally {
      setBaixando(false)
    }
  }

  return (
    <>
      <div className="dr-b">
        <p className="lbl">Formato</p>
        <label className="opt recomendado">
          <input type="radio" name="fmt" value="xlsx" checked={formato === 'xlsx'} onChange={() => setFormato('xlsx')} />
          <span>
            <b>
              XLSX <span className="selo-rec">Recomendado para planilha</span>
            </b>
            <small>Abre no Excel e no LibreOffice com números e acentos certos</small>
          </span>
        </label>
        <label className="opt">
          <input type="radio" name="fmt" value="csv" checked={formato === 'csv'} onChange={() => setFormato('csv')} />
          <span>
            <b>CSV</b>
            <small>Texto separado por vírgula, em UTF-8 com BOM, para outros programas</small>
          </span>
        </label>
        <p className="lbl">Escopo</p>
        <label className="opt">
          <input type="radio" name="esc" value="ano" checked={escopo === 'ano'} onChange={() => setEscopo('ano')} />
          <span>
            <b>Ano selecionado</b>
            <small>{anoInteiro}, todos os cenários</small>
          </span>
        </label>
        <label className="opt">
          <input type="radio" name="esc" value="serie" checked={escopo === 'serie'} onChange={() => setEscopo('serie')} />
          <span>
            <b>Série completa</b>
            <small>2026 a 2070</small>
          </span>
        </label>
        <div className="note-box">
          Cada linha traz um cenário com os indicadores, a decomposição dos efeitos, os controles de simulação e a coluna de origem.
        </div>
      </div>
      <div className="dr-f">
        <button type="button" className="btn pri wide" disabled={baixando} onClick={confirmar}>
          <Icone nome="down" />
          Exportar
        </button>
      </div>
    </>
  )
}

const TITULOS = { fontes: ['db', 'Fonte dos dados'], api: ['api', 'Contrato da API'], exportar: ['down', 'Exportar dados'] }

export default function Gaveta({ tipo, ano, localidade = 'Brasil', simulacao = PADRAO_SIMULACAO, aoFechar, avisar, exportar }) {
  const ref = useRef(null)
  const anterior = useRef(null)
  const fechar = useRef(aoFechar)
  fechar.current = aoFechar

  useEffect(() => {
    anterior.current = document.activeElement
    ref.current?.focus()
    const tecla = (e) => {
      if (e.key === 'Escape') fechar.current()
      if (e.key === 'Tab' && ref.current) {
        const focaveis = [...ref.current.querySelectorAll('button,input,select,[tabindex="0"]')]
        if (!focaveis.length) return
        const [primeiro, ultimo] = [focaveis[0], focaveis[focaveis.length - 1]]
        if (e.shiftKey && document.activeElement === primeiro) {
          ultimo.focus()
          e.preventDefault()
        } else if (!e.shiftKey && document.activeElement === ultimo) {
          primeiro.focus()
          e.preventDefault()
        }
      }
    }
    document.addEventListener('keydown', tecla)
    return () => {
      document.removeEventListener('keydown', tecla)
      anterior.current?.focus?.()
    }
  }, [])

  const [icone, titulo] = TITULOS[tipo]
  return (
    <>
      <div className="scrim" onClick={aoFechar} />
      <aside className="drawer" role="dialog" aria-modal="true" aria-labelledby="drT" tabIndex={-1} ref={ref}>
        <Cabecalho icone={icone} titulo={titulo} aoFechar={aoFechar} />
        {tipo === 'fontes' && <Fontes />}
        {tipo === 'api' && <Api ano={ano} localidade={localidade} simulacao={simulacao} avisar={avisar} />}
        {tipo === 'exportar' && (
          <Exportar ano={ano} localidade={localidade} simulacao={simulacao} aoFechar={aoFechar} avisar={avisar} exportar={exportar} />
        )}
      </aside>
    </>
  )
}
