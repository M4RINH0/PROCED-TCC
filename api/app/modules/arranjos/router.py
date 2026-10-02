from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core import obter_cliente
from app.modules.arranjos.repository import RepositorioArranjos, RepositorioSupabase
from app.modules.arranjos.schemas import ArranjosResposta, Grupo
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
