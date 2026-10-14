"""Núcleo metodológico do TCC: equações eq:tec, eq:tbc e eq:tbc-pd, ponte de
domicílios pelas taxas de chefia (premissa P2) e reponderação da amostra.

Funções puras, sem banco nem rede. Toda média usa o peso amostral da POF
(`peso_final`); com peso 1 em todos os domicílios, vira a média simples.

    TEC_x   = soma(peso * consumo per capita) / soma(peso)    faixa x do chefe
    TBC     = a mesma média, sem distinção de faixa
    TBC_pd  = soma_x (TEC_x * nDom_x,s) / soma_x nDom_x,s
    chefia_c       = soma(peso da célula c) / Pop_x,2018      c = (faixa x, arranjo)
    nDom_c,s       = chefia_c * Pop_x,s
    consumo total  = soma_c nDom_c,s * consumo médio por domicílio_c
    calibrado      = consumo por pessoa * população do IBGE no ano (P12)
"""

from collections.abc import Hashable, Iterable, Mapping
from dataclasses import dataclass


def _validar_razao(consumo: float, domicilios: float) -> None:
    if consumo < 0:
        raise ValueError("o consumo não pode ser negativo")
    if domicilios <= 0:
        raise ValueError("o número de domicílios precisa ser maior que zero")


def tec(cedpercap_x: float, dom_x: float) -> float:
    """Taxa específica de consumo da faixa x: soma ponderada do consumo per capita
    dividida pela soma dos pesos (com peso 1, pela contagem de domicílios)."""
    _validar_razao(cedpercap_x, dom_x)
    return cedpercap_x / dom_x


def tbc(cedpercap: float, dom: float) -> float:
    """Taxa bruta de consumo, sem distinção de idade."""
    _validar_razao(cedpercap, dom)
    return cedpercap / dom


def media_ponderada(valores: Iterable[float], pesos: Iterable[float]) -> float:
    """soma(peso * valor) / soma(peso). Serve para a TEC, a TBC e o consumo médio por domicílio."""
    valores, pesos = list(valores), list(pesos)
    if len(valores) != len(pesos):
        raise ValueError("valores e pesos precisam ter o mesmo tamanho")
    if any(p < 0 for p in pesos):
        raise ValueError("o peso não pode ser negativo")
    total = sum(pesos)
    if total <= 0:
        raise ValueError("a soma dos pesos precisa ser maior que zero")
    return sum(v * p for v, p in zip(valores, pesos)) / total


def tbc_pd(tec_por_faixa: Mapping[Hashable, float], ndom_por_faixa: Mapping[Hashable, float]) -> float:
    """Taxa bruta padronizada pela estrutura de domicílios do cenário s.

    As duas entradas precisam ter exatamente as mesmas chaves (faixas, ou células
    de faixa e arranjo).
    """
    if set(tec_por_faixa) != set(ndom_por_faixa):
        raise ValueError("as faixas de TEC e de domicílios do cenário precisam ser as mesmas")
    if not tec_por_faixa:
        raise ValueError("informe ao menos uma faixa etária")
    if any(v < 0 for v in tec_por_faixa.values()):
        raise ValueError("a TEC não pode ser negativa")
    if any(n < 0 for n in ndom_por_faixa.values()):
        raise ValueError("o número de domicílios não pode ser negativo")
    total = sum(ndom_por_faixa.values())
    if total <= 0:
        raise ValueError("o total de domicílios do cenário precisa ser maior que zero")
    return sum(tec_por_faixa[x] * ndom_por_faixa[x] for x in tec_por_faixa) / total


def taxas_chefia(
    pesos_por_celula: Mapping[tuple[str, str], float], populacao_ref_por_faixa: Mapping[str, float]
) -> dict[tuple[str, str], float]:
    """Premissa P2: domicílios ponderados da célula (faixa, arranjo) / população da faixa no ano de referência."""
    chefia = {}
    for (faixa, arranjo), peso in pesos_por_celula.items():
        if peso < 0:
            raise ValueError("a soma dos pesos não pode ser negativa")
        populacao = populacao_ref_por_faixa.get(faixa, 0)
        if populacao <= 0:
            raise ValueError(f"falta a população da faixa {faixa} no ano de referência")
        chefia[(faixa, arranjo)] = peso / populacao
    return chefia


def domicilios_projetados(
    chefia: Mapping[tuple[str, str], float], populacao_ano_por_faixa: Mapping[str, float]
) -> dict[tuple[str, str], float]:
    """nDom_c,s = taxa de chefia da célula * população da faixa no ano s."""
    if any(p < 0 for p in populacao_ano_por_faixa.values()):
        raise ValueError("a população não pode ser negativa")
    return {celula: taxa * populacao_ano_por_faixa.get(celula[0], 0) for celula, taxa in chefia.items()}


def consumo_total(ndom: Mapping[Hashable, float], consumo_medio_domicilio: Mapping[Hashable, float]) -> float:
    """Domicílios projetados vezes o consumo médio por domicílio de cada célula.

    Nunca população vezes consumo per capita.
    """
    if set(ndom) != set(consumo_medio_domicilio):
        raise ValueError("as células de domicílios e de consumo precisam ser as mesmas")
    if any(n < 0 for n in ndom.values()) or any(c < 0 for c in consumo_medio_domicilio.values()):
        raise ValueError("domicílios e consumo não podem ser negativos")
    return sum(ndom[c] * consumo_medio_domicilio[c] for c in ndom)


def moradores_projetados(ndom: Mapping[Hashable, float], moradores_medios: Mapping[Hashable, float]) -> float:
    """Domicílios projetados vezes a média ponderada de moradores de cada célula."""
    return consumo_total(ndom, moradores_medios)


def consumo_por_pessoa(consumo: float, moradores: float) -> float:
    """Consumo total dividido pelos moradores projetados."""
    _validar_razao(consumo, moradores)
    return consumo / moradores


def reponderar(
    pesos: Iterable[float], celulas: Iterable[Hashable], alvo_por_celula: Mapping[Hashable, float]
) -> list[float]:
    """Ajusta o peso de cada domicílio para que a soma da sua célula seja o alvo:

        peso'_i = peso_i * alvo_c / soma_{j em c} peso_j
    """
    pesos, celulas = list(pesos), list(celulas)
    if len(pesos) != len(celulas):
        raise ValueError("pesos e células precisam ter o mesmo tamanho")
    if any(p < 0 for p in pesos):
        raise ValueError("o peso não pode ser negativo")
    soma: dict[Hashable, float] = {}
    for p, c in zip(pesos, celulas):
        soma[c] = soma.get(c, 0.0) + p
    sem_alvo = set(soma) - set(alvo_por_celula)
    if sem_alvo:
        raise ValueError(f"células sem alvo: {sorted(map(str, sem_alvo))}")
    vazias = [c for c, s in soma.items() if s <= 0 and alvo_por_celula[c] > 0]
    if vazias:
        raise ValueError(f"células com alvo e sem peso na amostra: {sorted(map(str, vazias))}")
    return [p * alvo_por_celula[c] / soma[c] if soma[c] > 0 else 0.0 for p, c in zip(pesos, celulas)]


def fator_calibracao(populacao: float, moradores: float) -> float:
    """Premissa P12: população do IBGE no ano dividida pelos moradores projetados de todas as células.

    É um fator único para todas as células: corrige o nível, mas não a composição.
    """
    if populacao < 0:
        raise ValueError("a população não pode ser negativa")
    if moradores <= 0:
        raise ValueError("os moradores projetados precisam ser maiores que zero")
    return populacao / moradores


# ---------- projeção por células (método das taxas e contrafactual) ----------


@dataclass(frozen=True)
class Celula:
    """Parâmetros de uma célula (faixa do chefe, arranjo) medidos na POF, fixos no horizonte."""

    amostra: int
    peso: float  # domicílios ponderados no ano de referência
    tec: float  # consumo per capita médio ponderado
    consumo_domicilio: float  # consumo médio ponderado por domicílio
    moradores: float  # moradores médios ponderados


def parametros_celulas(registros: Iterable[tuple[Hashable, float, float, float, float]]) -> dict[Hashable, Celula]:
    """Agrupa (célula, peso, consumo do domicílio, consumo per capita, moradores) em médias ponderadas."""
    somas: dict[Hashable, list[float]] = {}
    for chave, peso, consumo, per_capita, moradores in registros:
        if peso <= 0:
            raise ValueError("o peso de cada domicílio precisa ser maior que zero")
        acc = somas.setdefault(chave, [0, 0.0, 0.0, 0.0, 0.0])
        acc[0] += 1
        acc[1] += peso
        acc[2] += peso * per_capita
        acc[3] += peso * consumo
        acc[4] += peso * moradores
    return {c: Celula(int(n), w, sp / w, sc / w, sm / w) for c, (n, w, sp, sc, sm) in somas.items()}


@dataclass(frozen=True)
class Resumo:
    domicilios: float
    moradores: float
    consumo_total: float  # bruto: diagnóstico, fora da API
    tbc_padronizada: float
    consumo_por_pessoa: float
    consumo_total_calibrado: float | None  # None sem população total do ano


TAXAS = "taxas"
CONTRAFACTUAL = "contrafactual"


class Projecao:
    """Ponte comum (P2) e cenários do método das taxas.

    taxas:          nDom_c,s = chefia_c * Pop_x,s
    contrafactual:  o total de domicílios do ano segue a projeção, e a distribuição
                    entre as células fica congelada na do ano-base (P10)
    """

    def __init__(
        self,
        celulas: Mapping[tuple[str, str], Celula],
        populacao_por_faixa: Mapping[int, Mapping[str, float]],
        ano_referencia: int,
        ano_base: int,
        populacao_total: Mapping[int, float] | None = None,
    ):
        if ano_referencia not in populacao_por_faixa:
            raise ValueError(f"falta a população de {ano_referencia}, ano de referência")
        if not celulas:
            raise ValueError("informe ao menos uma célula")
        self.celulas = dict(celulas)
        self.populacao_por_faixa = populacao_por_faixa
        self.populacao_total = populacao_total or {}
        self.ano_base = ano_base
        self.chefia = taxas_chefia({c: p.peso for c, p in self.celulas.items()}, populacao_por_faixa[ano_referencia])

    def domicilios(self, ano: int, cenario: str = TAXAS) -> dict[tuple[str, str], float]:
        if ano not in self.populacao_por_faixa:
            raise KeyError(ano)
        projetados = domicilios_projetados(self.chefia, self.populacao_por_faixa[ano])
        if cenario == TAXAS:
            return projetados
        if cenario == CONTRAFACTUAL:
            return congelar_composicao(self.domicilios(self.ano_base), sum(projetados.values()))
        raise ValueError(f"cenário desconhecido: {cenario}")

    def resumo(self, ano: int, cenario: str = TAXAS, chaves: Iterable[tuple[str, str]] | None = None) -> Resumo | None:
        """Indicadores do ano no conjunto de células `chaves` (todas, se None); None se ele não tiver domicílios.

        O fator de calibração usa os moradores de todas as células, para o recorte
        somar exatamente o total calibrado do país.
        """
        todos = self.domicilios(ano, cenario)
        sub = {c: todos[c] for c in (self.celulas if chaves is None else chaves) if c in todos}
        if sum(sub.values()) <= 0:
            return None
        consumo = consumo_total(sub, {c: self.celulas[c].consumo_domicilio for c in sub})
        moradores = moradores_projetados(sub, {c: self.celulas[c].moradores for c in sub})
        por_pessoa = consumo_por_pessoa(consumo, moradores)
        calibrado = None
        if ano in self.populacao_total:
            moradores_todos = moradores_projetados(todos, {c: self.celulas[c].moradores for c in todos})
            calibrado = consumo * fator_calibracao(self.populacao_total[ano], moradores_todos)
        return Resumo(
            domicilios=sum(sub.values()),
            moradores=moradores,
            consumo_total=consumo,
            tbc_padronizada=tbc_pd({c: self.celulas[c].tec for c in sub}, sub),
            consumo_por_pessoa=por_pessoa,
            consumo_total_calibrado=calibrado,
        )


def congelar_composicao(base: Mapping[Hashable, float], total: float) -> dict[Hashable, float]:
    """Distribui `total` entre as células na proporção de `base` (contrafactual, P10)."""
    soma = sum(base.values())
    if soma <= 0:
        raise ValueError("a composição de base precisa ter domicílios")
    if total < 0:
        raise ValueError("o total de domicílios não pode ser negativo")
    return {c: n / soma * total for c, n in base.items()}
