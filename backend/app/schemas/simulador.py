from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.estrutura_etaria import FaixaConsumo
from app.schemas.panorama import Simulacao

FONTE = "POF 2017 a 2018 (média ponderada pelo peso amostral), tendência das POFs 2002 a 2003 e 2008 a 2009 e Projeções da População (IBGE)"


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
    taxas = "taxas"  # método das taxas com a tendência dos arranjos (P13)
    taxas_arranjos_fixos = "taxas_arranjos_fixos"  # só o envelhecimento, arranjos congelados em 2026
    contrafactual = "contrafactual"  # composição de domicílios de 2026 congelada


class SimulacaoResposta(Simulacao):
    ano: int
    faixa: str
    arranjo: ArranjoSim
    base: BaseSim
    valor: float | None = Field(description="TEC ponderada da célula, kWh/mês por pessoa; igual nos dois cenários (P6)")
    motivo_sem_valor: str | None
    domicilios_amostra: int
    baixa_confiabilidade: bool = Field(description="menos de 30 domicílios na amostra da POF")
    domicilios_projetados: float | None = Field(default=None, description="domicílios da célula no ano e no cenário")
    participacao_pct: float | None = Field(default=None, description="participação da célula no total de domicílios do ano")
    consumo_total_calibrado_kwh_mes: float | None = Field(
        default=None, description="consumo total da célula calibrado pela população do IBGE (P12), kWh/mês"
    )
    por_faixa: list[FaixaConsumo]
    recuperado: bool = Field(
        default=False,
        description="true quando o resultado veio de um cenário já calculado e salvo (RF09); false quando foi calculado agora",
    )
    unidade: Literal["kWh/mes/pessoa"] = "kWh/mes/pessoa"
    fonte: str = FONTE
    localidade: str = "Brasil"
