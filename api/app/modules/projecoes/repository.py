"""Fontes de valores das projeções.

Enquanto o esquema do banco não existe, o único repositório disponível é o
ilustrativo, que reproduz as funções sintéticas de prototipo/proced.html.
Os valores dele NÃO decorrem de apuração e saem com dados_ilustrativos=True.
"""

import math
from typing import Protocol

from app.modules.projecoes.schemas import ANO_FINAL, ANO_INICIAL, CenarioId, Recorte


class RepositorioProjecoes(Protocol):
    dados_ilustrativos: bool

    def valor(self, cenario: CenarioId, ano: int, recorte: Recorte) -> float | None: ...


def _forma(ano: int, k: float = 7.2) -> float:
    """Curva logística normalizada: 0 em 2026, 1 em 2075."""
    t = (ano - ANO_INICIAL) / (ANO_FINAL - ANO_INICIAL)

    def s(x: float) -> float:
        return 1 / (1 + math.exp(-k * (x - 0.5)))

    return (s(t) - s(0)) / (s(1) - s(0))


class RepositorioIlustrativo:
    dados_ilustrativos = True

    def valor(self, cenario: CenarioId, ano: int, recorte: Recorte) -> float | None:
        fator = 1.0 if recorte is Recorte.chefe_60_mais else 0.8
        s = _forma(ano)
        if cenario is CenarioId.mod:
            return (158.4 + 71.9 * s) * fator
        if cenario is CenarioId.ibge:
            return (157.9 + 50.2 * s) * fator
        return (159.2 + 103.1 * s) * fator
