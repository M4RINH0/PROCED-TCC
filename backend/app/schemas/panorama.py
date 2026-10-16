from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from app.dominio import ANO_FINAL, ANO_INICIAL, Recorte

FONTE = "POF 2002 a 2003, 2008 a 2009 e 2017 a 2018 e Projeções da População (IBGE)"
UNIDADE = "kWh/mes/pessoa"


class CenarioId(str, Enum):
    taxas = "taxas"  # método das taxas com a tendência dos arranjos (P13)
    taxas_arranjos_fixos = "taxas_arranjos_fixos"  # só o envelhecimento: arranjos congelados em 2026
    contrafactual = "contrafactual"  # composição de domicílios de 2026 congelada (P10)


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
    participacao_consumo_pct: float | None = Field(
        default=None, description="participação do recorte no consumo residencial de todos os domicílios da localidade, %"
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


class Simulacao(BaseModel):
    intensidade: float = Field(default=0.6, description="intensidade da tendência dos arranjos depois de 2026 (0 = congelados; padrão calibrado 0,6)")
    k: float = Field(default=1.0, description="velocidade do envelhecimento (1 = projeção do IBGE)")
    simulacao: bool = Field(default=False, description="algum controle fora do padrão: o resultado é uma simulação")


class Efeitos(BaseModel):
    """Decomposição: envelhecimento = idade + arranjos (taxas menos contrafactual)."""

    efeito_envelhecimento_kwh: float | None = Field(default=None, description="taxas menos contrafactual, na TBC padronizada")
    efeito_idade_kwh: float | None = Field(default=None, description="taxas_arranjos_fixos menos contrafactual")
    efeito_arranjos_kwh: float | None = Field(default=None, description="taxas menos taxas_arranjos_fixos")
    efeito_envelhecimento_total_kwh_mes: float | None = Field(default=None, description="o mesmo, no consumo total calibrado")
    efeito_idade_total_kwh_mes: float | None = None
    efeito_arranjos_total_kwh_mes: float | None = None
    efeito_envelhecimento_participacao_pp: float | None = Field(default=None, description="o mesmo, na participação, em pontos percentuais")
    efeito_idade_participacao_pp: float | None = None
    efeito_arranjos_participacao_pp: float | None = None


class ProjecaoResposta(Amostra, Simulacao, Efeitos):
    ano: int = Field(ge=ANO_INICIAL, le=ANO_FINAL)
    recorte: Recorte
    unidade: Literal["kWh/mes/pessoa"] = UNIDADE
    cenarios: list[Cenario]
    dados_ilustrativos: bool
    fonte: str = FONTE
    localidade: str = "Brasil"


class PontoSerie(Efeitos):
    ano: int
    cenarios: list[Cenario]
    participacao_60_mais_pct: float | None = Field(description="pessoas de 60 anos ou mais na população; null se o ano não estiver na projeção")


class SerieResposta(Amostra, Simulacao):
    recorte: Recorte
    unidade: Literal["kWh/mes/pessoa"] = UNIDADE
    pontos: list[PontoSerie]
    dados_ilustrativos: bool
    fonte: str = FONTE
    localidade: str = "Brasil"
