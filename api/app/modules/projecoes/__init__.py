"""Módulo projecoes: RF01, RF02 e RF11.

Interface pública. Outros módulos importam só daqui.
"""

from app.modules.projecoes.calculo import tbc, tbc_pd, tec
from app.modules.projecoes.repository import RepositorioProjecoes
from app.modules.projecoes.router import obter_repositorio, router
from app.modules.projecoes.schemas import (
    ANO_FINAL,
    ANO_FINAL_IBGE,
    ANO_INICIAL,
    FONTE,
    FaixaConsumo,
    FiltroArranjo,
    Recorte,
)
from app.modules.projecoes.service import obter_consumo_por_faixa

__all__ = [
    "router",
    "obter_repositorio",
    "obter_consumo_por_faixa",
    "RepositorioProjecoes",
    "tec",
    "tbc",
    "tbc_pd",
    "Recorte",
    "FiltroArranjo",
    "FaixaConsumo",
    "FONTE",
    "ANO_INICIAL",
    "ANO_FINAL",
    "ANO_FINAL_IBGE",
]
