import { useEffect, useState } from 'react'
import { ROTAS } from './rotas.js'
import { lerTema, salvarTema, temaEfetivo } from './tema.js'
import { useRotaHash } from './useRotaHash.js'

const prefereEscuro = () => globalThis.matchMedia?.('(prefers-color-scheme: dark)').matches ?? false

function Logo() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <rect x="2" y="2" width="20" height="20" rx="6" fill="#F2B01E" />
      <path d="M13 5.5 7.5 13.2h4.1l-1 5.3 5.8-7.9h-4.2z" fill="#1D1603" />
    </svg>
  )
}

export default function App() {
  const [rota, navegar] = useRotaHash()
  const [tema, setTema] = useState(() => temaEfetivo(lerTema(), prefereEscuro()))
  const atual = ROTAS.find((r) => r.id === rota)

  useEffect(() => {
    document.documentElement.dataset.theme = tema
  }, [tema])

  const alternarTema = () => {
    const novo = tema === 'dark' ? 'light' : 'dark'
    salvarTema(novo)
    setTema(novo)
  }

  return (
    <>
      <header className="top">
        <div className="brand">
          <Logo />
          <b>PROCED</b>
        </div>
        <nav className="tabs" aria-label="Análises">
          {ROTAS.map((r) => (
            <button
              key={r.id}
              type="button"
              className="tab"
              aria-current={r.id === rota ? 'page' : undefined}
              onClick={() => navegar(r.id)}
            >
              {r.titulo}
            </button>
          ))}
        </nav>
        <div className="acts">
          <span className="illus">Dados ilustrativos</span>
          <button type="button" className="ib" onClick={alternarTema}>
            {tema === 'dark' ? 'Tema claro' : 'Tema escuro'}
          </button>
        </div>
      </header>
      <main>
        <atual.Tela />
      </main>
    </>
  )
}
