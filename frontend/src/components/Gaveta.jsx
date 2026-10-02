import { useEffect, useRef } from 'react'
import { useConsulta } from '../hooks/useConsulta.js'
import { buscarFontes, buscarProjecao } from '../services/api.js'
import Icone from './Icone.jsx'

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
        {(dados ?? []).map((f) => (
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
      <div className="note-box">
        A API lê o banco no Supabase só pelo back-end. Premissas adotadas e regras de derivação estão em docs/premissas.md e
        docs/banco-supabase.md.
      </div>
    </div>
  )
}

function Api({ ano, avisar }) {
  const params = { ano: Math.round(ano), recorte: 'chefe_60_mais' }
  const { status, dados } = useConsulta((o) => buscarProjecao(params, o), [params.ano])
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
            /projecoes?ano={params.ano}&amp;recorte={params.recorte}
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

function Exportar({ ano, aoFechar, avisar }) {
  return (
    <>
      <div className="dr-b">
        <p className="lbl">Formato</p>
        <label className="opt">
          <input type="radio" name="fmt" defaultChecked />
          <span>
            <b>CSV</b>
            <small>Texto separado por vírgula</small>
          </span>
        </label>
        <label className="opt">
          <input type="radio" name="fmt" />
          <span>
            <b>XLSX</b>
            <small>Planilha</small>
          </span>
        </label>
        <p className="lbl">Escopo</p>
        <label className="opt">
          <input type="radio" name="esc" defaultChecked />
          <span>
            <b>Ano selecionado</b>
            <small>{Math.round(ano)}, três cenários</small>
          </span>
        </label>
        <label className="opt">
          <input type="radio" name="esc" />
          <span>
            <b>Série completa</b>
            <small>2026 a 2075</small>
          </span>
        </label>
        <div className="note-box">
          Cada valor sai acompanhado da coluna de origem. Anos posteriores a 2070 vêm com a célula da projeção oficial vazia.
          A exportação (RF08) ainda não tem endpoint na API.
        </div>
      </div>
      <div className="dr-f">
        <button
          type="button"
          className="btn pri wide"
          onClick={() => {
            aoFechar()
            avisar('Exportação ainda não implementada (RF08)')
          }}
        >
          <Icone nome="down" />
          Exportar
        </button>
      </div>
    </>
  )
}

const TITULOS = { fontes: ['db', 'Fonte dos dados'], api: ['api', 'Contrato da API'], exportar: ['down', 'Exportar dados'] }

export default function Gaveta({ tipo, ano, aoFechar, avisar }) {
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
        {tipo === 'api' && <Api ano={ano} avisar={avisar} />}
        {tipo === 'exportar' && <Exportar ano={ano} aoFechar={aoFechar} avisar={avisar} />}
      </aside>
    </>
  )
}
