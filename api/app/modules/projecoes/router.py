from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core import obter_cliente
from app.modules.projecoes.repository import RepositorioProjecoes, RepositorioSupabase
from app.modules.projecoes.schemas import ANO_FINAL, ANO_INICIAL, ProjecaoResposta, Recorte, SerieResposta
from app.modules.projecoes.service import obter_projecao, obter_serie

router = APIRouter(prefix="/projecoes", tags=["projecoes"])


@lru_cache
def obter_repositorio() -> RepositorioProjecoes:
    return RepositorioSupabase(obter_cliente())


Repositorio = Annotated[RepositorioProjecoes, Depends(obter_repositorio)]
ParamRecorte = Annotated[Recorte, Query(description="Grupo de domicílios mononucleares")]


@router.get("", response_model=ProjecaoResposta, summary="Projeção dos cenários num ano")
def consultar_projecao(
    ano: Annotated[int, Query(ge=ANO_INICIAL, le=ANO_FINAL, description="Ano de 2026 a 2075")],
    recorte: ParamRecorte,
    repositorio: Repositorio,
) -> ProjecaoResposta:
    return obter_projecao(ano, recorte, repositorio)


@router.get("/serie", response_model=SerieResposta, summary="Série dos cenários de 2026 a 2075")
def consultar_serie(recorte: ParamRecorte, repositorio: Repositorio) -> SerieResposta:
    return obter_serie(recorte, repositorio)
