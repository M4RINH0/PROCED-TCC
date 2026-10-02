"""Rotas da página Panorama (RF01, RF11)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dados import Dados, obter_dados
from app.dominio import ANO_FINAL, ANO_INICIAL, Recorte
from app.schemas.panorama import ProjecaoResposta, SerieResposta
from app.services.panorama import obter_projecao, obter_serie

router = APIRouter(prefix="/projecoes", tags=["panorama"])

DadosDep = Annotated[Dados, Depends(obter_dados)]
ParamRecorte = Annotated[Recorte, Query(description="Grupo de domicílios mononucleares")]


@router.get("", response_model=ProjecaoResposta, summary="Projeção dos cenários num ano")
def consultar_projecao(
    ano: Annotated[int, Query(ge=ANO_INICIAL, le=ANO_FINAL, description="Ano de 2026 a 2070")],
    recorte: ParamRecorte,
    dados: DadosDep,
) -> ProjecaoResposta:
    return obter_projecao(ano, recorte, dados)


@router.get("/serie", response_model=SerieResposta, summary="Série dos cenários de 2026 a 2070")
def consultar_serie(recorte: ParamRecorte, dados: DadosDep) -> SerieResposta:
    return obter_serie(recorte, dados)
