import { useCallback, useEffect, useState } from 'react'
import { rotaDoHash } from './rotas.js'

export function useRotaHash() {
  const [rota, setRota] = useState(() => rotaDoHash(window.location.hash))

  useEffect(() => {
    const aoMudar = () => setRota(rotaDoHash(window.location.hash))
    window.addEventListener('hashchange', aoMudar)
    return () => window.removeEventListener('hashchange', aoMudar)
  }, [])

  const navegar = useCallback((id) => {
    window.location.hash = id
    setRota(rotaDoHash(id))
  }, [])

  return [rota, navegar]
}
