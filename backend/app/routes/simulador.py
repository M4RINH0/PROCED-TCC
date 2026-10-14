"""Rotas da página Simulador (RF07)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dados import Dados, obter_dados
from app.dominio import ANO_FINAL, ANO_INICIAL, Localidade
from app.schemas.simulador import ArranjoSim, BaseSim, FaixaSim, SimulacaoResposta
from app.services.simulador import simular

router = APIRouter(prefix="/simulador", tags=["simulador"])


@router.get("", response_model=SimulacaoResposta, summary="Consumo projetado de um tipo de domicílio num ano")
def consultar_simulacao(
    ano: Annotated[int, Query(ge=ANO_INICIAL, le=ANO_FINAL, description="Ano de 2026 a 2070")],
    faixa: Annotated[FaixaSim, Query(description="Faixa etária do chefe")],
    arranjo: Annotated[ArranjoSim, Query()],
    base: Annotated[BaseSim, Query(description="Cenário: taxas ou contrafactual")],
    dados: Annotated[Dados, Depends(obter_dados)],
    localidade: Annotated[Localidade, Query(description="Brasil, região ou sigla da UF")] = Localidade.Brasil,
) -> SimulacaoResposta:
    return simular(ano, faixa, arranjo, base, dados, localidade.value)
