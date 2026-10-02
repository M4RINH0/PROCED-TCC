from typing import Literal

from pydantic import BaseModel

from app.modules.projecoes import FaixaConsumo, FiltroArranjo

ANO_INICIAL_PIRAMIDE = 2026
ANO_FINAL_PIRAMIDE = 2070  # fim da projeção populacional do IBGE

FONTE_PIRAMIDE = "Projeções da População (IBGE), Brasil"
FONTE_CONSUMO = "POF 2017 a 2018 (IBGE), média dos domicílios da amostra"


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


class PiramidesResposta(BaseModel):
    piramides: list[PiramideResposta]
    fonte: str = FONTE_PIRAMIDE
