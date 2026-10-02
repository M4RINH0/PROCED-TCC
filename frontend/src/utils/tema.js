/* Preferência de tema do visitante. Falha de armazenamento nunca quebra a tela. */
const CHAVE = 'pe-theme'

export function lerTema(armazenamento = globalThis.localStorage) {
  try {
    const valor = armazenamento?.getItem(CHAVE)
    return valor === 'light' || valor === 'dark' ? valor : null
  } catch {
    return null
  }
}

export function salvarTema(tema, armazenamento = globalThis.localStorage) {
  try {
    armazenamento?.setItem(CHAVE, tema)
  } catch {
    /* sem armazenamento: o tema vale só nesta visita */
  }
}

export function temaEfetivo(atributo, prefereEscuro) {
  if (atributo === 'light' || atributo === 'dark') return atributo
  return prefereEscuro ? 'dark' : 'light'
}
