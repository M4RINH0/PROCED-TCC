from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.modules.projecoes.repository import RepositorioIlustrativo, RepositorioProjecoes
from app.modules.projecoes.schemas import ANO_FINAL, ANO_INICIAL, ProjecaoResposta, Recorte
from app.modules.projecoes.service import obter_projecao

router = APIRouter(prefix="/projecoes", tags=["projecoes"])


def obter_repositorio() -> RepositorioProjecoes:
    return RepositorioIlustrativo()


@router.get("", response_model=ProjecaoResposta, summary="Projeção dos cenários num ano")
def consultar_projecao(
    ano: Annotated[int, Query(ge=ANO_INICIAL, le=ANO_FINAL, description="Ano de 2026 a 2075")],
    recorte: Annotated[Recorte, Query(description="Grupo de domicílios")],
    repositorio: Annotated[RepositorioProjecoes, Depends(obter_repositorio)],
) -> ProjecaoResposta:
    return obter_projecao(ano, recorte, repositorio)
