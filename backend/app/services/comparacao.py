"""Regras da página Comparar (RF12): de 2 a 6 grupos de domicílios no mesmo indicador e cenário.

Cada grupo é um conjunto de células (faixa do chefe, arranjo), e os valores vêm de
Projecao.resumo, o mesmo cálculo do Panorama: os agregados mono_60, mono_59 e todos_60
reproduzem os recortes chefe_60_mais, mononuclear_abaixo_60 e chefe_60_mais_todos.
- domicilios: domicílios projetados do grupo (P2 e P13);
- consumo_total: consumo total calibrado pela população do IBGE (P12);
- participacao: consumo do grupo sobre o de todos os domicílios da localidade;
- consumo_por_pessoa: consumo total sobre os moradores projetados (P11), só para agregados,
  porque o de uma célula isolada fica nos níveis da POF e não muda com o tempo (P6).
O índice divide o valor do ano pelo de 2026 e multiplica por 100.
"""

from collections.abc import Sequence

from app.calculo import Resumo, indice, variacao
from app.dominio import (
    ANO_FINAL,
    ANO_INICIAL,
    BRASIL,
    CASAL_OU_DUPLA,
    GRUPOS,
    INTENSIDADE_PADRAO,
    K_PADRAO,
    MAXIMO_GRUPOS,
    MINIMO_GRUPOS,
    MULTIPESSOAL,
    UNIPESSOAL,
    GrupoId,
    baixa_confiabilidade,
    base_da_localidade,
    celulas_do_grupo,
    em_simulacao,
    faixas_da_idade,
    projecao_da_base,
    tendencia_dos_dados,
)
from app.schemas.comparacao import (
    ArranjoGrupo,
    ComparacaoResposta,
    FormaComparacao,
    IndicadorComparacao,
    LinhaComparacao,
    PontoGrupo,
    SerieGrupo,
)
from app.schemas.panorama import CenarioId

ANOS_TABELA = (ANO_INICIAL, 2050, ANO_FINAL)

UNIDADES = {
    IndicadorComparacao.domicilios: "domicílios",
    IndicadorComparacao.consumo_total: "kWh/mês",
    IndicadorComparacao.participacao: "% do consumo residencial",
    IndicadorComparacao.consumo_por_pessoa: "kWh/mês por pessoa",
}
# casas decimais de cada indicador, as mesmas do Panorama (None: inteiro)
CASAS = {
    IndicadorComparacao.domicilios: None,
    IndicadorComparacao.consumo_total: None,
    IndicadorComparacao.participacao: 2,
    IndicadorComparacao.consumo_por_pessoa: 1,
}
ARRANJO_DA_CELULA = {UNIPESSOAL: ArranjoGrupo.unipessoal, CASAL_OU_DUPLA: ArranjoGrupo.casal_ou_dupla, MULTIPESSOAL: ArranjoGrupo.multipessoal}

SEM_POR_PESSOA = (
    "O consumo por pessoa de uma célula isolada fica nos níveis da POF e não muda com o tempo; "
    "compare agregados para ver o efeito da composição."
)
SEM_AMOSTRA = "Falta amostra da POF em alguma faixa do grupo nesta localidade."


def validar_grupos(grupos: Sequence[GrupoId]) -> list[GrupoId]:
    lista = list(grupos)
    if not MINIMO_GRUPOS <= len(lista) <= MAXIMO_GRUPOS:
        raise ValueError(f"escolha de {MINIMO_GRUPOS} a {MAXIMO_GRUPOS} grupos")
    if len(set(lista)) != len(lista):
        raise ValueError("cada grupo pode aparecer uma vez só")
    return lista


def _arredondar(valor: float | None, casas: int | None) -> float | None:
    if valor is None:
        return None
    return round(valor) if casas is None else round(valor, casas)


def valor_do_indicador(resumo: Resumo | None, indicador: IndicadorComparacao) -> float | None:
    """Valor sem arredondar do indicador num resumo da projeção."""
    if resumo is None:
        return None
    if indicador == IndicadorComparacao.domicilios:
        return resumo.domicilios
    if indicador == IndicadorComparacao.consumo_total:
        return resumo.consumo_total_calibrado
    if indicador == IndicadorComparacao.participacao:
        return None if resumo.participacao_consumo is None else resumo.participacao_consumo * 100
    return resumo.consumo_por_pessoa


def ordem_de_crescimento(variacoes_pct: Sequence[float | None]) -> list[int | None]:
    """1 para a maior variação percentual; grupos sem variação ficam sem ordem."""
    com_valor = sorted((v, i) for i, v in enumerate(variacoes_pct) if v is not None)
    ordem: list[int | None] = [None] * len(variacoes_pct)
    for posicao, (_, i) in enumerate(reversed(com_valor), start=1):
        ordem[i] = posicao
    return ordem


def _serie(grupo: GrupoId, projecao, amostra: dict, anos_com_populacao: set[int], cenario: CenarioId, indicador, forma):
    g = GRUPOS[grupo]
    celulas = celulas_do_grupo(grupo)
    n = sum(amostra.get(c, 0) for c in celulas)
    # como no Panorama: sem domicílio da amostra numa faixa do grupo, a projeção do grupo não fecha
    completo = all(any(amostra.get((f.rotulo, a), 0) for a in g.arranjos) for f in faixas_da_idade(g.chefe_60_mais))
    motivo = None
    if indicador == IndicadorComparacao.consumo_por_pessoa and not g.agregado:
        motivo = SEM_POR_PESSOA
    elif projecao is None or not completo:
        motivo = SEM_AMOSTRA
    brutos: dict[int, float | None] = {}
    for ano in range(ANO_INICIAL, ANO_FINAL + 1):
        if motivo or ano not in anos_com_populacao:
            brutos[ano] = None
            continue
        brutos[ano] = valor_do_indicador(projecao.resumo(ano, cenario.value, celulas), indicador)
    base = brutos.get(ANO_INICIAL)
    pontos = []
    for ano, bruto in brutos.items():
        absoluto = _arredondar(bruto, CASAS[indicador])
        ind = _arredondar(indice(bruto, base), 1)
        pontos.append(PontoGrupo(ano=ano, valor=ind if forma == FormaComparacao.indice else absoluto, valor_absoluto=absoluto, indice=ind))
    serie = SerieGrupo(
        id=grupo,
        rotulo=g.rotulo,
        agregado=g.agregado,
        chefe_60_mais=g.chefe_60_mais,
        arranjo=None if g.agregado else ARRANJO_DA_CELULA[g.arranjos[0]],
        domicilios_amostra=n,
        baixa_confiabilidade=any(baixa_confiabilidade(amostra.get(c, 0)) for c in celulas),
        motivo_sem_valor=motivo,
        pontos=pontos,
    )
    return serie, brutos


def obter_comparacao(
    grupos: Sequence[GrupoId],
    dados,
    indicador: IndicadorComparacao = IndicadorComparacao.domicilios,
    forma: FormaComparacao = FormaComparacao.indice,
    cenario: CenarioId = CenarioId.taxas,
    localidade: str = BRASIL,
    intensidade: float = INTENSIDADE_PADRAO,
    k: float = K_PADRAO,
) -> ComparacaoResposta:
    grupos = validar_grupos(grupos)
    base = base_da_localidade(dados, localidade)
    populacao = dados.populacao_por_idade(localidade)
    projecao = projecao_da_base(base, tendencia_dos_dados(dados), intensidade, k) if base else None
    amostra = {c: p.amostra for c, p in base.celulas.items()} if base else {}
    anos = set(populacao)
    if cenario == CenarioId.contrafactual and ANO_INICIAL not in anos:
        anos = set()  # o contrafactual congela a composição de 2026

    series, brutos = [], []
    for grupo in grupos:
        serie, bruto = _serie(grupo, projecao, amostra, anos, cenario, indicador, forma)
        series.append(serie)
        brutos.append(bruto)

    variacoes = [variacao(b.get(ANO_INICIAL), b.get(ANO_FINAL)) for b in brutos]
    ordens = ordem_de_crescimento([v[1] for v in variacoes])
    casas = CASAS[indicador]
    tabela = [
        LinhaComparacao(
            id=s.id,
            rotulo=s.rotulo,
            valor_2026=_arredondar(b.get(ANOS_TABELA[0]), casas),
            valor_2050=_arredondar(b.get(ANOS_TABELA[1]), casas),
            valor_2070=_arredondar(b.get(ANOS_TABELA[2]), casas),
            variacao_absoluta=_arredondar(v[0], casas),
            variacao_pct=_arredondar(v[1], 1),
            ordem=o,
        )
        for s, b, v, o in zip(series, brutos, variacoes, ordens)
    ]
    return ComparacaoResposta(
        indicador=indicador,
        forma=forma,
        cenario=cenario,
        unidade=UNIDADES[indicador],
        localidade=localidade,
        grupos=series,
        tabela=tabela,
        intensidade=intensidade,
        k=k,
        simulacao=em_simulacao(intensidade, k),
    )
