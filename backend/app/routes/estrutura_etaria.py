"""Rotas da página Estrutura etária (RF05, RF06)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dados import Dados, obter_dados
from app.dominio import ANO_FINAL, ANO_INICIAL, FiltroArranjo
from app.schemas.estrutura_etaria import ConsumoChefeResposta, PiramideResposta, PiramidesResposta
from app.services.estrutura_etaria import obter_consumo_chefe, obter_piramide, obter_piramides

router = APIRouter(prefix="/estrutura-etaria", tags=["estrutura etária"])

DadosDep = Annotated[Dados, Depends(obter_dados)]


@router.get("/piramide", response_model=PiramideResposta, summary="Pirâmide etária do Brasil num ano")
def consultar_piramide(
    ano: Annotated[int, Query(ge=ANO_INICIAL, le=ANO_FINAL, description="Ano de 2026 a 2070")],
    dados: DadosDep,
) -> PiramideResposta:
    return obter_piramide(ano, dados)


@router.get("/piramides", response_model=PiramidesResposta, summary="Pirâmides etárias do Brasil, 2026 a 2070")
def consultar_piramides(dados: DadosDep) -> PiramidesResposta:
    return obter_piramides(dados)


@router.get("/consumo-chefe", response_model=ConsumoChefeResposta, summary="Consumo por faixa etária do chefe")
def consultar_consumo_chefe(
    dados: DadosDep,
    arranjo: Annotated[FiltroArranjo, Query()] = FiltroArranjo.mononucleares,
) -> ConsumoChefeResposta:
    return obter_consumo_chefe(arranjo, dados)
