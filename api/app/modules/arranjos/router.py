from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core import obter_cliente
from app.modules import projecoes
from app.modules.arranjos.composicao import montar_composicao
from app.modules.arranjos.repository import RepositorioArranjos, RepositorioSupabase
from app.modules.arranjos.schemas import ArranjosResposta, ComposicaoResposta, Grupo
from app.modules.arranjos.service import obter_arranjos

router = APIRouter(prefix="/arranjos", tags=["arranjos"])


@lru_cache
def obter_repositorio() -> RepositorioArranjos:
    return RepositorioSupabase(obter_cliente())


@router.get("", response_model=ArranjosResposta, summary="Consumo por arranjo domiciliar")
def consultar_arranjos(
    repositorio: Annotated[RepositorioArranjos, Depends(obter_repositorio)],
    grupo: Annotated[Grupo, Query(description="Idade do chefe")] = Grupo.todos,
) -> ArranjosResposta:
    return obter_arranjos(grupo, repositorio)


@router.get("/composicao", response_model=ComposicaoResposta, summary="Composição dos domicílios por arranjo, 2026 a 2070")
def consultar_composicao(
    repositorio: Annotated[projecoes.RepositorioProjecoes, Depends(projecoes.obter_repositorio)],
) -> ComposicaoResposta:
    return montar_composicao(projecoes.obter_estrutura_domicilios(repositorio))
