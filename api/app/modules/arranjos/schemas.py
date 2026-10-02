from enum import Enum
from typing import Literal

from pydantic import BaseModel

FONTE = "POF 2017 a 2018 (IBGE), médias das UFs ponderadas pelo tamanho da amostra"


class Grupo(str, Enum):
    todos = "todos"
    chefe_60_mais = "chefe_60_mais"
    abaixo_60 = "abaixo_60"


class ArranjoConsumo(BaseModel):
    arranjo: str
    mononuclear: bool
    chefe_60_mais: bool
    domicilios_amostra: int
    consumo_per_capita_kwh: float
    consumo_total_kwh: float
    gasto_rs: float


class ArranjosResposta(BaseModel):
    grupo: Grupo
    unidade: Literal["kWh/mes/pessoa"] = "kWh/mes/pessoa"
    arranjos: list[ArranjoConsumo]
    fonte: str = FONTE


FONTE_COMPOSICAO = (
    "POF 2017 a 2018 e Projeções da População (IBGE); taxa de chefia de 2018 constante por faixa e arranjo"
)


class CategoriaComposicao(BaseModel):
    id: str
    arranjo: str
    chefe_60_mais: bool
    mononuclear: bool
    domicilios_amostra: int
    consumo_per_capita_kwh: float | None
    participacao_pct: list[float]  # um valor por ano, na ordem de anos
    casas: list[int]  # de cada 100 domicílios, por ano (soma 100)


class ComposicaoResposta(BaseModel):
    anos: list[int]
    categorias: list[CategoriaComposicao]
    fonte: str = FONTE_COMPOSICAO
