import { useEffect, useState } from 'react'

/* Devolve o valor só depois de `espera` ms sem mudanças (debounce): os controles de simulação
   não disparam uma consulta a cada passo */
export function useAdiado(valor, espera) {
  const [adiado, setAdiado] = useState(valor)
  useEffect(() => {
    const t = setTimeout(() => setAdiado(valor), espera)
    return () => clearTimeout(t)
  }, [valor, espera])
  return adiado
}
