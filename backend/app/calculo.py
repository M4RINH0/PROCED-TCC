"""Núcleo metodológico do TCC: equações eq:tec, eq:tbc e eq:tbc-pd.

Funções puras, sem banco nem rede.

    TEC_x   = CEDpercap_x / Dom_x
    TBC     = CEDpercap / Dom
    TBC_pd  = soma_x (TEC_x * nDom_x,s) / soma_x nDom_x,s
"""

from collections.abc import Mapping


def _validar_razao(consumo: float, domicilios: float) -> None:
    if consumo < 0:
        raise ValueError("o consumo não pode ser negativo")
    if domicilios <= 0:
        raise ValueError("o número de domicílios precisa ser maior que zero")


def tec(cedpercap_x: float, dom_x: float) -> float:
    """Taxa específica de consumo da faixa etária x do chefe."""
    _validar_razao(cedpercap_x, dom_x)
    return cedpercap_x / dom_x


def tbc(cedpercap: float, dom: float) -> float:
    """Taxa bruta de consumo, sem distinção de idade."""
    _validar_razao(cedpercap, dom)
    return cedpercap / dom


def tbc_pd(tec_por_faixa: Mapping[str, float], ndom_por_faixa: Mapping[str, float]) -> float:
    """Taxa bruta padronizada pela estrutura de domicílios do cenário s.

    As duas entradas precisam ter exatamente as mesmas faixas.
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
