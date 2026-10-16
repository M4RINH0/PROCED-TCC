/* Baixa um arquivo recebido da API (exportação RF08) com o nome sugerido */
export function salvarBlob(blob, nomeArquivo) {
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
