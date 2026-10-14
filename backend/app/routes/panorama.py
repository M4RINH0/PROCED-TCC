"""Rotas da página Panorama (RF01, RF02, RF11)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dados import Dados, obter_dados
from app.dominio import (
    ANO_FINAL,
    ANO_INICIAL,
    INTENSIDADE_MAXIMA,
    INTENSIDADE_MINIMA,
    INTENSIDADE_PADRAO,
    K_MAXIMO,
    K_MINIMO,
    K_PADRAO,
    Localidade,
    Recorte,
)
from app.schemas.panorama import ProjecaoResposta, SerieResposta
from app.services.panorama import obter_projecao, obter_serie

router = APIRouter(prefix="/projecoes", tags=["panorama"])

DadosDep = Annotated[Dados, Depends(obter_dados)]
ParamRecorte = Annotated[Recorte, Query(description="Grupo de domicílios exibido")]
ParamIntensidade = Annotated[
    float,
    Query(
        ge=INTENSIDADE_MINIMA,
        le=INTENSIDADE_MAXIMA,
        description="Intensidade da tendência dos arranjos: 0 congela os arranjos, 1 é a tendência observada (padrão)",
    ),
]
ParamK = Annotated[
    float, Query(ge=K_MINIMO, le=K_MAXIMO, description="Velocidade do envelhecimento: 1 é a projeção do IBGE (padrão)")
]

ParamLocalidade = Annotated[Localidade, Query(description="Brasil, região ou sigla da UF")]


@router.get("", response_model=ProjecaoResposta, summary="Projeção dos cenários num ano")
def consultar_projecao(
    ano: Annotated[int, Query(ge=ANO_INICIAL, le=ANO_FINAL, description="Ano de 2026 a 2070")],
    recorte: ParamRecorte,
    dados: DadosDep,
    localidade: ParamLocalidade = Localidade.Brasil,
    intensidade: ParamIntensidade = INTENSIDADE_PADRAO,
    k: ParamK = K_PADRAO,
) -> ProjecaoResposta:
    return obter_projecao(ano, recorte, dados, localidade.value, intensidade, k)


@router.get("/serie", response_model=SerieResposta, summary="Série dos cenários de 2026 a 2070")
def consultar_serie(
    recorte: ParamRecorte,
    dados: DadosDep,
    localidade: ParamLocalidade = Localidade.Brasil,
    intensidade: ParamIntensidade = INTENSIDADE_PADRAO,
    k: ParamK = K_PADRAO,
) -> SerieResposta:
    return obter_serie(recorte, dados, localidade.value, intensidade, k)
