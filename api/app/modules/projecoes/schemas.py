from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

ANO_INICIAL = 2026
ANO_FINAL = 2075
ANO_FINAL_IBGE = 2070  # a projeção oficial do IBGE termina aqui
ANO_REFERENCIA_POF = 2018  # POF 2017 a 2018

FONTE = "POF 2017 a 2018 e Projeções da População (IBGE)"
UNIDADE = "kWh/mes/pessoa"


class Recorte(str, Enum):
    chefe_60_mais = "chefe_60_mais"
    mononuclear_abaixo_60 = "mononuclear_abaixo_60"


class FiltroArranjo(str, Enum):
    mononucleares = "mononucleares"  # unipessoal e casal ou dupla
    unipessoal = "unipessoal"
    casal_ou_dupla = "casal_ou_dupla"
    multipessoal = "multipessoal"
    todos = "todos"


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


class FaixaConsumo(BaseModel):
    faixa: str
    domicilios_amostra: int
    consumo_per_capita_kwh: float | None = Field(description="TEC da faixa; null sem domicílios na amostra")
