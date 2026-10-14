"""Regras de Domicílios (RF03, RF04): consumo por arranjo e composição dos domicílios no tempo.

Toda média usa o peso amostral da POF (peso_final), sobre a tabela fato já sem as
linhas repetidas (P8).
"""

import math
from collections.abc import Iterable

from app.calculo import media_ponderada
from app.dados import Domicilio
from app.dominio import (
    ANO_FINAL,
    ANO_INICIAL,
    ANO_REFERENCIA_POF,
    ARRANJOS,
    BRASIL,
    CASAL_OU_DUPLA,
    FAIXAS_CHEFE,
    IDADE_IDOSO,
    MONONUCLEARES,
    MULTIPESSOAL,
    UNIPESSOAL,
    baixa_confiabilidade,
    celula_do_domicilio,
    da_localidade,
    montar_projecao,
    tendencia_nacional,
)
from app.schemas.domicilios import ArranjoConsumo, ArranjosResposta, CategoriaComposicao, ComposicaoResposta, Grupo

# ---------- consumo por arranjo ----------


def _no_grupo(chefe_60_mais: bool, grupo: Grupo) -> bool:
    return grupo is Grupo.todos or (grupo is Grupo.chefe_60_mais) == chefe_60_mais


def agregar(domicilios: Iterable[Domicilio], grupo: Grupo) -> list[ArranjoConsumo]:
    """Médias ponderadas por arranjo e por chefe de 60 anos ou mais."""
    grupos: dict[tuple[str, bool], list[Domicilio]] = {}
    for d in domicilios:
        chave = (d.arranjo, d.idade_chefe >= IDADE_IDOSO)
        if _no_grupo(chave[1], grupo):
            grupos.setdefault(chave, []).append(d)

    def ordem(chave):
        arranjo, idoso = chave
        return (ARRANJOS.index(arranjo) if arranjo in ARRANJOS else len(ARRANJOS), not idoso)

    resultado = []
    for (arranjo, idoso) in sorted(grupos, key=ordem):
        g = grupos[(arranjo, idoso)]
        pesos = [d.peso for d in g]
        com_gasto = [d for d in g if d.gasto_rs is not None]
        resultado.append(
            ArranjoConsumo(
                arranjo=arranjo,
                mononuclear=arranjo in MONONUCLEARES,
                chefe_60_mais=idoso,
                domicilios_amostra=len(g),
                baixa_confiabilidade=baixa_confiabilidade(len(g)),
                consumo_per_capita_kwh=round(media_ponderada([d.consumo_per_capita_kwh for d in g], pesos), 1),
                consumo_total_kwh=round(
                    media_ponderada([_consumo_total(d) for d in g], pesos), 1
                ),
                gasto_rs=(
                    round(media_ponderada([d.gasto_rs for d in com_gasto], [d.peso for d in com_gasto]), 2)
                    if com_gasto
                    else None
                ),
            )
        )
    return resultado


def _consumo_total(d: Domicilio) -> float:
    return d.consumo_total_kwh if d.consumo_total_kwh is not None else d.consumo_per_capita_kwh * (d.moradores or 1)


def obter_arranjos(grupo: Grupo, dados, localidade: str = BRASIL) -> ArranjosResposta:
    domicilios = da_localidade(dados.domicilios(), localidade)
    return ArranjosResposta(grupo=grupo, arranjos=agregar(domicilios, grupo), localidade=localidade)


# ---------- composição dos domicílios no tempo ----------


class EstruturaDomicilios:
    """Domicílios por faixa do chefe e arranjo no ano s, com a taxa de chefia de 2018
    da faixa constante (premissa P2) e a tendência dos arranjos (P13). Usa a mesma projeção do Panorama.
    """

    def __init__(
        self,
        domicilios: Iterable[Domicilio],
        populacao: dict[int, dict[int, int]],
        tendencia: dict[str, tuple[float, float]] | None = None,
    ):
        if ANO_REFERENCIA_POF not in populacao:
            raise ValueError(f"falta a população de {ANO_REFERENCIA_POF}, ano de referência da POF")
        lista = [d for d in domicilios if celula_do_domicilio(d) is not None]
        self.populacao = populacao
        self.projecao = montar_projecao(lista, populacao, tendencia) if lista else None
        self.amostra = {c: p.amostra for c, p in self.projecao.celulas.items()} if self.projecao else {}

    def no_ano(self, ano: int) -> dict[tuple[str, str], float] | None:
        """(faixa, arranjo) -> domicílios estimados; None sem projeção para o ano."""
        if ano not in self.populacao or self.projecao is None:
            return None
        return self.projecao.domicilios(ano)

    def tec_do_grupo(self, faixas: Iterable[str], arranjo: str) -> tuple[int, float | None]:
        """Domicílios da amostra e TEC ponderada de um arranjo num conjunto de faixas."""
        celulas = [self.projecao.celulas[(f, arranjo)] for f in faixas if self.projecao and (f, arranjo) in self.projecao.celulas]
        n = sum(c.amostra for c in celulas)
        if not celulas:
            return 0, None
        return n, media_ponderada([c.tec for c in celulas], [c.peso for c in celulas])

    def baixa_confiabilidade(self, faixas: Iterable[str], arranjo: str) -> bool:
        """Alguma célula do grupo tem menos de 30 domicílios na amostra (inclusive nenhum)."""
        return any(baixa_confiabilidade(self.amostra.get((f, arranjo), 0)) for f in faixas)


FAIXAS_60 = [f.rotulo for f in FAIXAS_CHEFE if f.minima >= 60]
FAIXAS_ABAIXO_60 = [f.rotulo for f in FAIXAS_CHEFE if f.minima < 60]

# ordem da grade: o recorte do estudo ocupa as primeiras casas
CATEGORIAS = (
    ("uni_60", UNIPESSOAL, True),
    ("cas_60", CASAL_OU_DUPLA, True),
    ("uni_59", UNIPESSOAL, False),
    ("cas_59", CASAL_OU_DUPLA, False),
    ("mul_60", MULTIPESSOAL, True),
    ("mul_59", MULTIPESSOAL, False),
)


def maior_resto(valores: list[float], total: int = 100) -> list[int]:
    """Arredonda proporções para inteiros que somam exatamente o total."""
    soma = sum(valores)
    if soma <= 0:
        return [0] * len(valores)
    brutos = [v / soma * total for v in valores]
    inteiros = [math.floor(b) for b in brutos]
    faltam = total - sum(inteiros)
    ordem = sorted(range(len(brutos)), key=lambda i: brutos[i] - inteiros[i], reverse=True)
    for i in ordem[:faltam]:
        inteiros[i] += 1
    return inteiros


def montar_composicao(estrutura: EstruturaDomicilios) -> ComposicaoResposta:
    anos, por_ano = [], []
    for ano in range(ANO_INICIAL, ANO_FINAL + 1):
        domicilios = estrutura.no_ano(ano)
        if domicilios is None:
            continue
        valores = []
        for _, arranjo, idoso in CATEGORIAS:
            faixas = FAIXAS_60 if idoso else FAIXAS_ABAIXO_60
            valores.append(sum(domicilios.get((f, arranjo), 0.0) for f in faixas))
        anos.append(ano)
        por_ano.append(valores)

    casas = [maior_resto(v) for v in por_ano]
    categorias = []
    for i, (ident, arranjo, idoso) in enumerate(CATEGORIAS):
        n, valor = estrutura.tec_do_grupo(FAIXAS_60 if idoso else FAIXAS_ABAIXO_60, arranjo)
        categorias.append(
            CategoriaComposicao(
                id=ident,
                arranjo=arranjo,
                chefe_60_mais=idoso,
                mononuclear=arranjo != MULTIPESSOAL,
                domicilios_amostra=n,
                baixa_confiabilidade=estrutura.baixa_confiabilidade(FAIXAS_60 if idoso else FAIXAS_ABAIXO_60, arranjo),
                consumo_per_capita_kwh=None if valor is None else round(valor, 1),
                participacao_pct=[round(v[i] / sum(v) * 100, 2) if sum(v) else 0.0 for v in por_ano],
                casas=[c[i] for c in casas],
            )
        )
    return ComposicaoResposta(anos=anos, categorias=categorias)


def obter_composicao(dados, localidade: str = BRASIL) -> ComposicaoResposta:
    domicilios = da_localidade(dados.domicilios(), localidade)
    tendencia = tendencia_nacional(dados.domicilios_historicos(), dados.domicilios())
    resposta = montar_composicao(EstruturaDomicilios(domicilios, dados.populacao_por_idade(localidade), tendencia))
    return resposta.model_copy(update={"localidade": localidade})
