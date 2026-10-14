from typing import Literal

from pydantic import BaseModel, Field

from app.dominio import FiltroArranjo

ANO_INICIAL_PIRAMIDE = 2026
ANO_FINAL_PIRAMIDE = 2070  # fim da projeção populacional do IBGE

FONTE_PIRAMIDE = "Projeções da População (IBGE)"
FONTE_CONSUMO = "POF 2017 a 2018 (IBGE), média ponderada pelo peso amostral"


class FaixaConsumo(BaseModel):
    faixa: str
    domicilios_amostra: int
    baixa_confiabilidade: bool = Field(default=False, description="menos de 30 domicílios na amostra da POF")
    consumo_per_capita_kwh: float | None = Field(description="TEC ponderada da faixa; null sem domicílios na amostra")


class FaixaPiramide(BaseModel):
    faixa: str
    homens_pct: float
    mulheres_pct: float


class PiramideResposta(BaseModel):
    ano: int
    faixas: list[FaixaPiramide]
    participacao_60_mais_pct: float
    fonte: str = FONTE_PIRAMIDE


class ConsumoChefeResposta(BaseModel):
    arranjo: FiltroArranjo
    unidade: Literal["kWh/mes/pessoa"] = "kWh/mes/pessoa"
    faixas: list[FaixaConsumo]
    fonte: str = FONTE_CONSUMO
    localidade: str = "Brasil"


class PiramidesResposta(BaseModel):
    piramides: list[PiramideResposta]
    fonte: str = FONTE_PIRAMIDE
    localidade: str = "Brasil"
    k: float = Field(default=1.0, description="velocidade do envelhecimento (1 = projeção do IBGE)")
    simulacao: bool = Field(default=False, description="k fora do padrão: a pirâmide é uma simulação")
