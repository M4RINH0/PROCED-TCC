/* Localidades vindas de GET /localidades: Brasil, regiões e estados (UFs) */
export const BRASIL = 'Brasil'

/* Região da localidade escolhida: o próprio nome se for região, a região da UF se for estado,
   null para o Brasil */
export function regiaoDe(regioes, valor) {
  if (!valor || valor === BRASIL) return null
  const regiao = regioes.find((r) => r.nome === valor || r.estados.some((e) => e.sigla === valor))
  return regiao?.nome ?? null
}

/* Nome para exibir: "Brasil", o nome da região ou o nome do estado */
export function nomeDaLocalidade(regioes, valor) {
  if (!valor || valor === BRASIL) return BRASIL
  for (const r of regioes) {
    if (r.nome === valor) return r.nome
    const estado = r.estados.find((e) => e.sigla === valor)
    if (estado) return estado.nome
  }
  return valor
}
