import { useCallback, useEffect, useRef, useState } from 'react'
import { Icone, definirFalhaSimulada } from '../shared/index.js'
import Gaveta from './Gaveta.jsx'
import LinhaDoTempo, { ANO_FINAL_IBGE, ANO_INICIAL } from './LinhaDoTempo.jsx'
import MenuDemonstracao from './MenuDemonstracao.jsx'
import { ROTAS } from './rotas.js'
import { lerTema, salvarTema, temaEfetivo } from './tema.js'
import { useRotaHash } from './useRotaHash.js'

const prefereEscuro = () => globalThis.matchMedia?.('(prefers-color-scheme: dark)').matches ?? false
const reduzMovimento = () => globalThis.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false

export default function App() {
  const [rota, navegar] = useRotaHash()
  const [tema, setTema] = useState(() => temaEfetivo(lerTema(), prefereEscuro()))
  const [ano, setAno] = useState(ANO_FINAL_IBGE)
  const [gaveta, setGaveta] = useState(null)
  const [falha, setFalha] = useState(false)
  const [recarga, setRecarga] = useState(0)
  const [aviso, setAviso] = useState('')
  const temporizador = useRef(0)
  const atual = ROTAS.find((r) => r.id === rota)

  useEffect(() => {
    document.documentElement.dataset.theme = tema
  }, [tema])

  /* abertura: o único movimento automático, o ano percorre 2026 a 2070 uma vez */
  useEffect(() => {
    if (reduzMovimento() || typeof requestAnimationFrame === 'undefined') return undefined
    const inicio = performance.now()
    let quadro = 0
    const passo = (agora) => {
      const p = Math.min(1, (agora - inicio) / 1500)
      setAno(ANO_INICIAL + (ANO_FINAL_IBGE - ANO_INICIAL) * (1 - Math.pow(1 - p, 3)))
      if (p < 1) quadro = requestAnimationFrame(passo)
      else setAno(ANO_FINAL_IBGE)
    }
    quadro = requestAnimationFrame(passo)
    return () => cancelAnimationFrame(quadro)
  }, [])

  const avisar = useCallback((texto) => {
    setAviso(texto)
    clearTimeout(temporizador.current)
    temporizador.current = setTimeout(() => setAviso(''), 2200)
  }, [])

  const alternarTema = () => {
    const novo = tema === 'dark' ? 'light' : 'dark'
    salvarTema(novo)
    setTema(novo)
  }

  const alternarFalha = () => {
    const nova = !falha
    definirFalhaSimulada(nova)
    setFalha(nova)
    setRecarga((r) => r + 1)
    avisar(nova ? 'Falha de conexão simulada' : 'Conexão restabelecida')
  }

  const escuro = tema === 'dark'
  return (
    <>
      <header className="top">
        <div className="brand">
          <Icone nome="logo" />
          <b>PROCED</b>
          <span className="bdesc">
            Projeção de Consumo por
            <br />
            Estrutura Demográfica
          </span>
        </div>
        <nav className="tabs" aria-label="Análises">
          {ROTAS.map((r) => (
            <button key={r.id} type="button" className="tab" aria-current={r.id === rota ? 'page' : undefined} onClick={() => navegar(r.id)}>
              <Icone nome={r.icone} />
              <span>{r.titulo}</span>
            </button>
          ))}
        </nav>
        <div className="acts">
          <span className="illus">
            <Icone nome="info" />
            Cenário do modelo pendente
          </span>
          <button type="button" className="ib" aria-label="Fonte dos dados" onClick={() => setGaveta('fontes')}>
            <Icone nome="db" />
            <span>Fontes</span>
          </button>
          <button type="button" className="ib" aria-label="Contrato da API" onClick={() => setGaveta('api')}>
            <Icone nome="api" />
            <span>API</span>
          </button>
          <button type="button" className="ib" aria-label="Exportar dados" onClick={() => setGaveta('exportar')}>
            <Icone nome="down" />
            <span>Exportar</span>
          </button>
          <MenuDemonstracao falha={falha} aoAlternarFalha={alternarFalha} aoReverCarregamento={() => setRecarga((r) => r + 1)} />
          <button type="button" className="ib" aria-label={escuro ? 'Usar tema claro' : 'Usar tema escuro'} onClick={alternarTema}>
            <Icone nome={escuro ? 'sun' : 'moon'} />
            <span>{escuro ? 'Tema claro' : 'Tema escuro'}</span>
          </button>
        </div>
      </header>
      <main className={atual.linhaDoTempo ? '' : 'nodock'}>
        <atual.Tela
          key={`${rota}-${recarga}`}
          ano={ano}
          aoMudarAno={setAno}
          abrirGaveta={setGaveta}
          avisar={avisar}
        />
      </main>
      <LinhaDoTempo ano={ano} aoMudarAno={setAno} oculta={!atual.linhaDoTempo} />
      {gaveta && <Gaveta tipo={gaveta} ano={ano} aoFechar={() => setGaveta(null)} avisar={avisar} />}
      <div className={aviso ? 'toast on' : 'toast'} role="status" aria-live="polite">
        {aviso}
      </div>
    </>
  )
}
