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
"""

from collections.abc import Hashable, Iterable, Mapping


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
