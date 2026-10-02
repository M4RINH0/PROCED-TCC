from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.modules import projecoes
from app.modules.simulador.schemas import ArranjoSim, BaseSim, FaixaSim, SimulacaoResposta
from app.modules.simulador.service import simular

router = APIRouter(prefix="/simulador", tags=["simulador"])


@router.get("", response_model=SimulacaoResposta, summary="Consumo projetado de um tipo de domicílio num ano")
def consultar_simulacao(
    ano: Annotated[int, Query(ge=projecoes.ANO_INICIAL, le=projecoes.ANO_FINAL, description="Ano de 2026 a 2075")],
    faixa: Annotated[FaixaSim, Query(description="Faixa etária do chefe")],
    arranjo: Annotated[ArranjoSim, Query()],
    base: Annotated[BaseSim, Query(description="Cenário de projeção")],
    repositorio: Annotated[projecoes.RepositorioProjecoes, Depends(projecoes.obter_repositorio)],
    taxa: Annotated[float | None, Query(ge=0, le=10, description="Taxa de envelhecimento anual; usada pelo cenário do modelo")] = None,
) -> SimulacaoResposta:
    return simular(ano, faixa, arranjo, base, taxa, repositorio)
