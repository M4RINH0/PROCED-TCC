from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from app.dominio import ANO_FINAL, ANO_INICIAL, Recorte

FONTE = "POF 2017 a 2018 e Projeções da População (IBGE)"
UNIDADE = "kWh/mes/pessoa"


class CenarioId(str, Enum):
    taxas = "taxas"  # método das taxas: padronização direta com a TEC ponderada da POF
    ml_rf = "ml_rf"  # Random Forest (pausado: sempre null)
    ml_gb = "ml_gb"  # Gradient Boosting (pausado: sempre null)
    contrafactual = "contrafactual"  # método das taxas com a composição de domicílios de 2026 congelada


class Cenario(BaseModel):
    id: CenarioId
    valor: float | None = Field(
        description="TBC padronizada: média por domicílio do consumo per capita, em kWh/mês por pessoa; "
        "null quando o cenário não tem dado"
    )
    consumo_por_pessoa_kwh: float | None = Field(
        default=None, description="consumo total do recorte dividido pelos moradores projetados, kWh/mês"
    )
    consumo_total_calibrado_kwh_mes: float | None = Field(
        default=None, description="consumo total do recorte calibrado pela população do IBGE (P12), kWh/mês"
    )
    variacao_kwh: float | None = Field(default=None, description="diferença do valor em relação a 2026 (só na série)")
    variacao_pct: float | None = Field(default=None, description="variação percentual do valor em relação a 2026 (só na série)")


class CelulaAmostra(BaseModel):
    faixa: str
    arranjo: str
    domicilios_amostra: int
    baixa_confiabilidade: bool = Field(description="menos de 30 domicílios na amostra da POF")


class Amostra(BaseModel):
    domicilios_amostra: int = Field(default=0, description="domicílios da POF no recorte e na localidade")
    celulas: list[CelulaAmostra] = Field(default_factory=list, description="amostra de cada célula do recorte")
    baixa_confiabilidade: bool = Field(default=False, description="alguma célula do recorte tem menos de 30 domicílios")


class ProjecaoResposta(Amostra):
    ano: int = Field(ge=ANO_INICIAL, le=ANO_FINAL)
    recorte: Recorte
    unidade: Literal["kWh/mes/pessoa"] = UNIDADE
    cenarios: list[Cenario]
    efeito_envelhecimento_kwh: float | None = Field(default=None, description="TBC padronizada de taxas menos a do contrafactual")
    efeito_envelhecimento_total_kwh_mes: float | None = Field(
        default=None, description="consumo total calibrado de taxas menos o do contrafactual"
    )
    dados_ilustrativos: bool
    fonte: str = FONTE
    localidade: str = "Brasil"


class PontoSerie(BaseModel):
    ano: int
    cenarios: list[Cenario]
    participacao_60_mais_pct: float | None = Field(description="pessoas de 60 anos ou mais na população; null se o ano não estiver na projeção")
    efeito_envelhecimento_kwh: float | None = Field(default=None, description="TBC padronizada de taxas menos a do contrafactual")
    efeito_envelhecimento_total_kwh_mes: float | None = Field(
        default=None, description="consumo total calibrado de taxas menos o do contrafactual"
    )


class SerieResposta(Amostra):
    recorte: Recorte
    unidade: Literal["kWh/mes/pessoa"] = UNIDADE
    pontos: list[PontoSerie]
    dados_ilustrativos: bool
    fonte: str = FONTE
    localidade: str = "Brasil"
