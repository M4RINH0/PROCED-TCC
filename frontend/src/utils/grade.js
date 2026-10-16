/* Disposição da grade de casas: quantas colunas e linhas usar para que n casas quadradas ocupem o
   maior espaço possível de uma área largura x altura. É só geometria da tela; os dados não mudam. */
export function melhorGrade(largura, altura, n = 100, minimoColunas = 5, maximoColunas = 25) {
  const gap = Math.max(3, Math.min(largura, altura) * 0.012)
  let melhor = null
  for (let colunas = minimoColunas; colunas <= maximoColunas; colunas++) {
    const linhas = Math.ceil(n / colunas)
    const celula = Math.min((largura - gap * (colunas - 1)) / colunas, (altura - gap * (linhas - 1)) / linhas)
    // em empate, a grade mais completa (menos casas faltando na última linha)
    if (!melhor || celula > melhor.celula + 0.01 || (Math.abs(celula - melhor.celula) <= 0.01 && linhas * colunas < melhor.linhas * melhor.colunas)) {
      melhor = { colunas, linhas, celula, gap }
    }
  }
  return melhor
}
