"""Rotas da gaveta Fontes (RF10)."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.dados import Dados, obter_dados
from app.schemas.fontes import FontesResposta
from app.services.fontes import obter_fontes

router = APIRouter(prefix="/fontes", tags=["fontes"])


@router.get("", response_model=FontesResposta, summary="Fontes, critério de exclusão, cobertura e premissas")
def listar_fontes(dados: Annotated[Dados, Depends(obter_dados)]) -> FontesResposta:
    return obter_fontes(dados)
