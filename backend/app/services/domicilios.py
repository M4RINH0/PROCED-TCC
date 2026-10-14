"""Regras de Domicílios (RF03, RF04): consumo por arranjo e composição dos domicílios no tempo."""

import math
from collections.abc import Iterable

from app.calculo import domicilios_projetados, taxas_chefia, tec
from app.dados import Domicilio
from app.dominio import (
    ANO_FINAL,
    ANO_INICIAL,
    ANO_REFERENCIA_POF,
    BRASIL,
    CASAL_OU_DUPLA,
    FAIXAS_CHEFE,
    MULTIPESSOAL,
    UNIPESSOAL,
    da_localidade,
    faixa_do_chefe,
    populacao_da_faixa,
    ufs_da_localidade,
)
from app.schemas.domicilios import ArranjoConsumo, ArranjosResposta, CategoriaComposicao, ComposicaoResposta, Grupo

# ---------- consumo por arranjo (tabela de coeficientes por UF) ----------
# A tabela traz médias por UF; a média nacional pondera cada UF pelo número de
# domicílios da amostra, o que equivale à média de todos os domicílios.

ORDEM = (UNIPESSOAL, CASAL_OU_DUPLA, MULTIPESSOAL)
MONONUCLEARES = {UNIPESSOAL, CASAL_OU_DUPLA}


def _no_grupo(chefe_60_mais: bool, grupo: Grupo) -> bool:
    return grupo is Grupo.todos or (grupo is Grupo.chefe_60_mais) == chefe_60_mais


def agregar(linhas: list[dict], grupo: Grupo) -> list[ArranjoConsumo]:
    soma: dict[tuple[str, bool], dict[str, float]] = {}
    for l in linhas:
        chave = (l["arranjo_familiar"], bool(l["is_60_mais"]))
        if not _no_grupo(chave[1], grupo):
            continue
        n = l["total_domicilios_amostra"]
        acc = soma.setdefault(chave, {"n": 0, "per_capita": 0.0, "total": 0.0, "gasto": 0.0})
        acc["n"] += n
        acc["per_capita"] += n * l["media_consumo_per_capita_kwh"]
        acc["total"] += n * l["media_consumo_total_kwh"]
        acc["gasto"] += n * l["media_gasto_rs"]

    def ordem(chave):
        arranjo, idoso = chave
        return (ORDEM.index(arranjo) if arranjo in ORDEM else len(ORDEM), not idoso)

    resultado = []
    for chave in sorted(soma, key=ordem):
        acc, (arranjo, idoso) = soma[chave], chave
        if acc["n"] <= 0:
            continue
        resultado.append(
            ArranjoConsumo(
                arranjo=arranjo,
                mononuclear=arranjo in MONONUCLEARES,
                chefe_60_mais=idoso,
                domicilios_amostra=int(acc["n"]),
                consumo_per_capita_kwh=round(tec(acc["per_capita"], acc["n"]), 1),
                consumo_total_kwh=round(acc["total"] / acc["n"], 1),
                gasto_rs=round(acc["gasto"] / acc["n"], 2),
            )
        )
    return resultado


def obter_arranjos(grupo: Grupo, dados, localidade: str = BRASIL) -> ArranjosResposta:
    ufs = ufs_da_localidade(localidade)
    linhas = [l for l in dados.coeficientes() if ufs is None or l["sigla_uf"] in ufs]
    return ArranjosResposta(grupo=grupo, arranjos=agregar(linhas, grupo), localidade=localidade)


# ---------- composição dos domicílios no tempo ----------


class EstruturaDomicilios:
    """Domicílios por faixa do chefe e arranjo no ano s, com a taxa de chefia de 2018
    constante em cada combinação (premissa P2 aplicada também ao arranjo).
    Taxa de chefia e TEC usam o peso amostral da POF (peso_final).
    """

    def __init__(self, domicilios: Iterable[Domicilio], populacao: dict[int, dict[int, int]]):
        if ANO_REFERENCIA_POF not in populacao:
            raise ValueError(f"falta a população de {ANO_REFERENCIA_POF}, ano de referência da POF")
        self.populacao = populacao
        self.amostra: dict[tuple[str, str], int] = {}
        self.peso: dict[tuple[str, str], float] = {}
        self.soma: dict[tuple[str, str], float] = {}  # soma de peso * consumo per capita
        for d in domicilios:
            faixa = faixa_do_chefe(d.idade_chefe)
            if faixa is None:
                continue
            chave = (faixa.rotulo, d.arranjo)
            self.amostra[chave] = self.amostra.get(chave, 0) + 1
            self.peso[chave] = self.peso.get(chave, 0.0) + d.peso
            self.soma[chave] = self.soma.get(chave, 0.0) + d.peso * d.consumo_per_capita_kwh
        self._faixas = {f.rotulo: f for f in FAIXAS_CHEFE}
        self.chefia = taxas_chefia(self.peso, self._populacao_por_faixa(ANO_REFERENCIA_POF))

    def _populacao_por_faixa(self, ano: int) -> dict[str, int]:
        return {r: populacao_da_faixa(self.populacao[ano], f) for r, f in self._faixas.items()}

    def no_ano(self, ano: int) -> dict[tuple[str, str], float] | None:
        """(faixa, arranjo) -> domicílios estimados; None sem projeção para o ano."""
        if ano not in self.populacao:
            return None
        return domicilios_projetados(self.chefia, self._populacao_por_faixa(ano))

    def tec_do_grupo(self, faixas: Iterable[str], arranjo: str) -> tuple[int, float | None]:
        """Domicílios da amostra e TEC ponderada de um arranjo num conjunto de faixas."""
        chaves = [(f, arranjo) for f in faixas if (f, arranjo) in self.amostra]
        n = sum(self.amostra[c] for c in chaves)
        peso = sum(self.peso[c] for c in chaves)
        return n, (tec(sum(self.soma[c] for c in chaves), peso) if peso > 0 else None)


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
                consumo_per_capita_kwh=None if valor is None else round(valor, 1),
                participacao_pct=[round(v[i] / sum(v) * 100, 2) if sum(v) else 0.0 for v in por_ano],
                casas=[c[i] for c in casas],
            )
        )
    return ComposicaoResposta(anos=anos, categorias=categorias)


def obter_composicao(dados, localidade: str = BRASIL) -> ComposicaoResposta:
    domicilios = da_localidade(dados.domicilios(), localidade)
    resposta = montar_composicao(EstruturaDomicilios(domicilios, dados.populacao_por_idade(localidade)))
    return resposta.model_copy(update={"localidade": localidade})
