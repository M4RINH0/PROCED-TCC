import { useCallback, useEffect, useState } from 'react'

/* Consulta à API com estados de carregamento, erro e nova tentativa.
   `buscar` recebe { signal } e devolve uma promessa; `chaves` refaz a consulta quando mudam. */
export function useConsulta(buscar, chaves) {
  const [estado, setEstado] = useState({ status: 'carregando', dados: null, erro: null })
  const [tentativa, setTentativa] = useState(0)

  useEffect(() => {
    const controle = new AbortController()
    setEstado((anterior) => ({ status: 'carregando', dados: anterior.dados, erro: null }))
    buscar({ signal: controle.signal })
      .then((dados) => setEstado({ status: 'ok', dados, erro: null }))
      .catch((erro) => {
        if (erro?.name !== 'AbortError') setEstado({ status: 'erro', dados: null, erro })
      })
    return () => controle.abort()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...chaves, tentativa])

  const recarregar = useCallback(() => setTentativa((t) => t + 1), [])
  return { ...estado, recarregar }
}
