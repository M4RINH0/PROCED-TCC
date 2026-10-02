"""Rotas da página Domicílios (RF03, RF04)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dados import Dados, obter_dados
from app.schemas.domicilios import ArranjosResposta, ComposicaoResposta, Grupo
from app.services.domicilios import obter_arranjos, obter_composicao

router = APIRouter(prefix="/arranjos", tags=["domicílios"])

DadosDep = Annotated[Dados, Depends(obter_dados)]


@router.get("", response_model=ArranjosResposta, summary="Consumo por arranjo domiciliar")
def consultar_arranjos(
    dados: DadosDep,
    grupo: Annotated[Grupo, Query(description="Idade do chefe")] = Grupo.todos,
) -> ArranjosResposta:
    return obter_arranjos(grupo, dados)


@router.get("/composicao", response_model=ComposicaoResposta, summary="Composição dos domicílios por arranjo, 2026 a 2070")
def consultar_composicao(dados: DadosDep) -> ComposicaoResposta:
    return obter_composicao(dados)
