"""Composição dos domicílios por arranjo ao longo dos anos (RF03, RF04)."""

import math

from app.modules.arranjos.schemas import CategoriaComposicao, ComposicaoResposta
from app.modules.projecoes import (
    ANO_FINAL_IBGE,
    ANO_INICIAL,
    CASAL_OU_DUPLA,
    FAIXAS_CHEFE,
    MULTIPESSOAL,
    UNIPESSOAL,
    EstruturaDomicilios,
)

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
    for ano in range(ANO_INICIAL, ANO_FINAL_IBGE + 1):
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
        n, tec = estrutura.tec_do_grupo(FAIXAS_60 if idoso else FAIXAS_ABAIXO_60, arranjo)
        categorias.append(
            CategoriaComposicao(
                id=ident,
                arranjo=arranjo,
                chefe_60_mais=idoso,
                mononuclear=arranjo != MULTIPESSOAL,
                domicilios_amostra=n,
                consumo_per_capita_kwh=None if tec is None else round(tec, 1),
                participacao_pct=[round(v[i] / sum(v) * 100, 2) if sum(v) else 0.0 for v in por_ano],
                casas=[c[i] for c in casas],
            )
        )
    return ComposicaoResposta(anos=anos, categorias=categorias)
