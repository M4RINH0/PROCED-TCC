from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core import obter_cliente
from app.modules import projecoes
from app.modules.estrutura_etaria.repository import RepositorioPiramide, RepositorioSupabase
from app.modules.estrutura_etaria.schemas import (
    ANO_FINAL_PIRAMIDE,
    ANO_INICIAL_PIRAMIDE,
    ConsumoChefeResposta,
    PiramideResposta,
    PiramidesResposta,
)
from app.modules.estrutura_etaria.service import obter_consumo_chefe, obter_piramide, obter_piramides

router = APIRouter(prefix="/estrutura-etaria", tags=["estrutura etária"])


@lru_cache
def obter_repositorio() -> RepositorioPiramide:
    return RepositorioSupabase(obter_cliente())


@router.get("/piramide", response_model=PiramideResposta, summary="Pirâmide etária do Brasil num ano")
def consultar_piramide(
    ano: Annotated[int, Query(ge=ANO_INICIAL_PIRAMIDE, le=ANO_FINAL_PIRAMIDE, description="Ano de 2026 a 2070")],
    repositorio: Annotated[RepositorioPiramide, Depends(obter_repositorio)],
) -> PiramideResposta:
    return obter_piramide(ano, repositorio)


@router.get("/piramides", response_model=PiramidesResposta, summary="Pirâmides etárias do Brasil, 2026 a 2070")
def consultar_piramides(
    repositorio: Annotated[RepositorioPiramide, Depends(obter_repositorio)],
) -> PiramidesResposta:
    return obter_piramides(repositorio, ANO_FINAL_PIRAMIDE)


@router.get("/consumo-chefe", response_model=ConsumoChefeResposta, summary="Consumo por faixa etária do chefe")
def consultar_consumo_chefe(
    repositorio: Annotated[projecoes.RepositorioProjecoes, Depends(projecoes.obter_repositorio)],
    arranjo: Annotated[projecoes.FiltroArranjo, Query()] = projecoes.FiltroArranjo.mononucleares,
) -> ConsumoChefeResposta:
    return obter_consumo_chefe(arranjo, repositorio)
