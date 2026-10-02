from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

ANO_INICIAL = 2026
ANO_FINAL = 2075
ANO_FINAL_IBGE = 2060  # a projeção oficial do IBGE termina aqui


class Recorte(str, Enum):
    chefe_60_mais = "chefe_60_mais"
    mononuclear_abaixo_60 = "mononuclear_abaixo_60"


class CenarioId(str, Enum):
    mod = "mod"  # projeção do modelo
    ibge = "ibge"  # projeção oficial do IBGE
    alt = "alt"  # cenário alternativo (ML)


class Cenario(BaseModel):
    id: CenarioId
    valor: float | None = Field(
        description="kWh/mês por pessoa; null quando não há dado (IBGE depois de 2060)"
    )


class ProjecaoResposta(BaseModel):
    ano: int = Field(ge=ANO_INICIAL, le=ANO_FINAL)
    recorte: Recorte
    unidade: Literal["kWh/mes/pessoa"] = "kWh/mes/pessoa"
    cenarios: list[Cenario]
    dados_ilustrativos: bool
