"""Rotas da página Simulador (RF02, RF07, RF09)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dados import Dados, obter_dados
from app.dominio import (
    ANO_FINAL,
    ANO_INICIAL,
    INTENSIDADE_MAXIMA,
    INTENSIDADE_MINIMA,
    INTENSIDADE_PADRAO,
    K_MAXIMO,
    K_MINIMO,
    K_PADRAO,
    Localidade,
)
from app.schemas.simulador import ArranjoSim, BaseSim, FaixaSim, SimulacaoResposta
from app.services.simulador import simular

router = APIRouter(prefix="/simulador", tags=["simulador"])

ParamIntensidade = Annotated[
    float,
    Query(
        ge=INTENSIDADE_MINIMA,
        le=INTENSIDADE_MAXIMA,
        description="Intensidade da tendência dos arranjos depois de 2026: 0 congela os arranjos (padrão calibrado 0,6)",
    ),
]
ParamK = Annotated[
    float, Query(ge=K_MINIMO, le=K_MAXIMO, description="Velocidade do envelhecimento: 1 é a projeção do IBGE (padrão)")
]


@router.get("", response_model=SimulacaoResposta, summary="Consumo projetado de um tipo de domicílio num ano")
def consultar_simulacao(
    ano: Annotated[int, Query(ge=ANO_INICIAL, le=ANO_FINAL, description="Ano de 2026 a 2070")],
    faixa: Annotated[FaixaSim, Query(description="Faixa etária do chefe")],
    arranjo: Annotated[ArranjoSim, Query()],
    base: Annotated[BaseSim, Query(description="Cenário: taxas, taxas_arranjos_fixos ou contrafactual")],
    dados: Annotated[Dados, Depends(obter_dados)],
    localidade: Annotated[Localidade, Query(description="Brasil, região ou sigla da UF")] = Localidade.Brasil,
    intensidade: ParamIntensidade = INTENSIDADE_PADRAO,
    k: ParamK = K_PADRAO,
    recalcular: Annotated[bool, Query(description="Força novo cálculo e atualiza o cenário salvo (RF09)")] = False,
) -> SimulacaoResposta:
    return simular(ano, faixa, arranjo, base, dados, localidade.value, intensidade, k, recalcular=recalcular)
