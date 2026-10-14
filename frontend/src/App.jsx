import { useCallback, useEffect, useRef, useState } from 'react'
import Gaveta from './components/Gaveta.jsx'
import Icone from './components/Icone.jsx'
import LinhaDoTempo, { ANO_FINAL, ANO_INICIAL } from './components/LinhaDoTempo.jsx'
import MenuDemonstracao from './components/MenuDemonstracao.jsx'
import { useAdiado } from './hooks/useAdiado.js'
import { useConsulta } from './hooks/useConsulta.js'
import { useRotaHash } from './hooks/useRotaHash.js'
import { ROTAS } from './rotas.js'
import { buscarLocalidades } from './services/api.js'
import { definirFalhaSimulada } from './services/http.js'
import { BRASIL, nomeDaLocalidade } from './utils/localidades.js'
import { ESPERA_MS, PADRAO_SIMULACAO, emSimulacao } from './utils/simulacao.js'
import { lerTema, salvarTema, temaEfetivo } from './utils/tema.js'

const prefereEscuro = () => globalThis.matchMedia?.('(prefers-color-scheme: dark)').matches ?? false
const reduzMovimento = () => globalThis.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false

export default function App() {
  const [rota, navegar] = useRotaHash()
  const [tema, setTema] = useState(() => temaEfetivo(lerTema(), prefereEscuro()))
  const [ano, setAno] = useState(ANO_FINAL)
  const [gaveta, setGaveta] = useState(null)
  const [falha, setFalha] = useState(false)
  const [recarga, setRecarga] = useState(0)
  const [aviso, setAviso] = useState('')
  const [localidade, setLocalidade] = useState(BRASIL)
  /* parâmetros de simulação (RF02): globais, preservados ao trocar de aba; as consultas usam os adiados */
  const [parametros, setParametros] = useState(PADRAO_SIMULACAO)
  const aplicados = useAdiado(parametros, ESPERA_MS)
  const listaLocalidades = useConsulta((o) => buscarLocalidades(o), [])
  const temporizador = useRef(0)
  const atual = ROTAS.find((r) => r.id === rota)

  useEffect(() => {
    document.documentElement.dataset.theme = tema
  }, [tema])

  /* abertura: o único movimento automático, o ano percorre o horizonte uma vez */
  useEffect(() => {
    if (reduzMovimento() || typeof requestAnimationFrame === 'undefined') return undefined
    const inicio = performance.now()
    let quadro = 0
    const passo = (agora) => {
      const p = Math.min(1, (agora - inicio) / 1500)
      setAno(ANO_INICIAL + (ANO_FINAL - ANO_INICIAL) * (1 - Math.pow(1 - p, 3)))
      if (p < 1) quadro = requestAnimationFrame(passo)
      else setAno(ANO_FINAL)
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

  const regioes = listaLocalidades.dados?.regioes ?? []
  const local = {
    valor: localidade,
    nome: nomeDaLocalidade(regioes, localidade),
    nomeDe: (valor) => nomeDaLocalidade(regioes, valor),
    regioes,
    aoMudar: setLocalidade,
  }
  const simulacao = {
    valores: parametros,
    aplicados,
    ativa: emSimulacao(parametros),
    aoMudar: (campo, valor) => setParametros((p) => ({ ...p, [campo]: valor })),
    restaurar: () => setParametros(PADRAO_SIMULACAO),
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
          local={local}
          simulacao={simulacao}
        />
      </main>
      <LinhaDoTempo ano={ano} aoMudarAno={setAno} oculta={!atual.linhaDoTempo} />
      {gaveta && (
        <Gaveta tipo={gaveta} ano={ano} localidade={localidade} simulacao={aplicados} aoFechar={() => setGaveta(null)} avisar={avisar} />
      )}
      <div className={aviso ? 'toast on' : 'toast'} role="status" aria-live="polite">
        {aviso}
      </div>
    </>
  )
}
