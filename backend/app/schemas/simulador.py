from enum import Enum
from typing import Literal

from pydantic import BaseModel

from app.schemas.estrutura_etaria import FaixaConsumo

FONTE = "POF 2017 a 2018 (IBGE), média dos domicílios da amostra"


class FaixaSim(str, Enum):
    ate_29 = "ate_29"
    de_30_a_39 = "30_39"
    de_40_a_49 = "40_49"
    de_50_a_59 = "50_59"
    de_60_a_69 = "60_69"
    de_70_a_79 = "70_79"
    mais_de_80 = "80_mais"


ROTULO_FAIXA = {
    FaixaSim.ate_29: "até 29",
    FaixaSim.de_30_a_39: "30 a 39",
    FaixaSim.de_40_a_49: "40 a 49",
    FaixaSim.de_50_a_59: "50 a 59",
    FaixaSim.de_60_a_69: "60 a 69",
    FaixaSim.de_70_a_79: "70 a 79",
    FaixaSim.mais_de_80: "80+",
}


class ArranjoSim(str, Enum):
    unipessoal = "unipessoal"
    casal_ou_dupla = "casal_ou_dupla"
    multipessoal = "multipessoal"


class BaseSim(str, Enum):
    mod = "mod"
    ibge = "ibge"
    alt = "alt"


class SimulacaoResposta(BaseModel):
    ano: int
    faixa: str
    arranjo: ArranjoSim
    base: BaseSim
    taxa: float | None
    valor: float | None
    motivo_sem_valor: str | None
    domicilios_amostra: int
    por_faixa: list[FaixaConsumo]
    unidade: Literal["kWh/mes/pessoa"] = "kWh/mes/pessoa"
    fonte: str = FONTE
