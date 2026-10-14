from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.panorama import Simulacao

FONTE = "POF 2017 a 2018 (IBGE), médias ponderadas pelo peso amostral"


class Grupo(str, Enum):
    todos = "todos"
    chefe_60_mais = "chefe_60_mais"
    abaixo_60 = "abaixo_60"


class ArranjoConsumo(BaseModel):
    arranjo: str
    mononuclear: bool
    chefe_60_mais: bool
    domicilios_amostra: int
    baixa_confiabilidade: bool = Field(description="menos de 30 domicílios na amostra da POF")
    consumo_per_capita_kwh: float
    consumo_total_kwh: float
    gasto_rs: float | None


class ArranjosResposta(BaseModel):
    grupo: Grupo
    unidade: Literal["kWh/mes/pessoa"] = "kWh/mes/pessoa"
    arranjos: list[ArranjoConsumo]
    fonte: str = FONTE
    localidade: str = "Brasil"


FONTE_COMPOSICAO = (
    "POF 2002 a 2003, 2008 a 2009 e 2017 a 2018 e Projeções da População (IBGE); taxa de chefia de 2018 "
    "constante por faixa e tendência dos arranjos"
)


class CategoriaComposicao(BaseModel):
    id: str
    arranjo: str
    chefe_60_mais: bool
    mononuclear: bool
    domicilios_amostra: int
    baixa_confiabilidade: bool = Field(default=False, description="alguma célula do grupo tem menos de 30 domicílios na amostra")
    consumo_per_capita_kwh: float | None
    participacao_pct: list[float]  # um valor por ano, na ordem de anos
    casas: list[int]  # de cada 100 domicílios, por ano (soma 100)


class ComposicaoResposta(Simulacao):
    anos: list[int]
    categorias: list[CategoriaComposicao]
    fonte: str = FONTE_COMPOSICAO
    localidade: str = "Brasil"
