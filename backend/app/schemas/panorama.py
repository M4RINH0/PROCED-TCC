from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from app.dominio import ANO_FINAL, ANO_INICIAL, Recorte

FONTE = "POF 2017 a 2018 e Projeções da População (IBGE)"
UNIDADE = "kWh/mes/pessoa"


class CenarioId(str, Enum):
    mod = "mod"  # projeção do modelo
    ibge = "ibge"  # projeção oficial do IBGE
    alt = "alt"  # cenário alternativo (ML)


class Cenario(BaseModel):
    id: CenarioId
    valor: float | None = Field(
        description="kWh/mês por pessoa; null quando não há dado (IBGE depois de 2070, cenário não modelado)"
    )
    variacao_kwh: float | None = Field(default=None, description="diferença em relação a 2026 (só na série)")
    variacao_pct: float | None = Field(default=None, description="variação percentual em relação a 2026 (só na série)")


class ProjecaoResposta(BaseModel):
    ano: int = Field(ge=ANO_INICIAL, le=ANO_FINAL)
    recorte: Recorte
    unidade: Literal["kWh/mes/pessoa"] = UNIDADE
    cenarios: list[Cenario]
    dados_ilustrativos: bool
    fonte: str = FONTE


class PontoSerie(BaseModel):
    ano: int
    cenarios: list[Cenario]
    participacao_60_mais_pct: float | None = Field(description="pessoas de 60 anos ou mais na população; null depois de 2070")
    amplitude_kwh: float | None = Field(default=None, description="maior menos menor valor entre os cenários com dado")
    modelo_menos_oficial_kwh: float | None = Field(default=None, description="mod menos ibge, quando os dois existem")


class SerieResposta(BaseModel):
    recorte: Recorte
    unidade: Literal["kWh/mes/pessoa"] = UNIDADE
    pontos: list[PontoSerie]
    dados_ilustrativos: bool
    fonte: str = FONTE
