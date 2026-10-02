import { useCallback, useEffect, useState } from 'react'
import { buscarProjecao } from '../api.js'

export function useProjecao({ ano, recorte }, buscar = buscarProjecao) {
  const [estado, setEstado] = useState({ status: 'carregando', dados: null })
  const [tentativa, setTentativa] = useState(0)

  useEffect(() => {
    const controle = new AbortController()
    setEstado((anterior) => ({ status: 'carregando', dados: anterior.dados }))
    buscar({ ano, recorte }, { signal: controle.signal })
      .then((dados) => setEstado({ status: 'ok', dados }))
      .catch((erro) => {
        if (erro?.name !== 'AbortError') setEstado({ status: 'erro', dados: null, erro })
      })
    return () => controle.abort()
  }, [ano, recorte, buscar, tentativa])

  const recarregar = useCallback(() => setTentativa((t) => t + 1), [])
  return { ...estado, recarregar }
}
